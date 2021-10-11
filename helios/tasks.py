"""
Celery queued tasks for Helios

2010-08-01
ben@adida.net
"""
import copy
from celery import shared_task
from celery.utils.log import get_logger

from . import signals
from .models import CastVote, Election, Voter, VoterFile, ElectionOfficer, ValidationPolicy
from .view_utils import render_template_raw

#added by John
from helios_auth.security import get_user
from helios.models import ValidationRequest
from helios_auth.models import User
import helios

@shared_task
def cast_vote_verify_and_store(cast_vote_id, status_update_message=None, **kwargs):
    cast_vote = CastVote.objects.get(id=cast_vote_id)
    result = cast_vote.verify_and_store()

    voter = cast_vote.voter
    election = voter.election
    user = voter.get_user()

    if result:
        # send the signal
        signals.vote_cast.send(sender=election, election=election, user=user, voter=voter, cast_vote=cast_vote)

        if status_update_message and user.can_update_status():
            user.update_status(status_update_message)
    else:
        logger = get_logger(cast_vote_verify_and_store.__name__)
        logger.error("Failed to verify and store %d" % cast_vote_id)


@shared_task
def voters_email(election_id, subject_template, body_template, extra_vars={},
                 voter_constraints_include=None, voter_constraints_exclude=None):
    """
    voter_constraints_include are conditions on including voters
    voter_constraints_exclude are conditions on excluding voters
    """
    election = Election.objects.get(id=election_id)

    # select the right list of voters
    voters = election.voter_set.all()
    if voter_constraints_include:
        voters = voters.filter(**voter_constraints_include)
    if voter_constraints_exclude:
        voters = voters.exclude(**voter_constraints_exclude)

    for voter in voters:
        single_voter_email.delay(voter.uuid, subject_template, body_template, extra_vars)


@shared_task
def voters_notify(election_id, notification_template, extra_vars={}):
    election = Election.objects.get(id=election_id)
    for voter in election.voter_set.all():
        single_voter_notify.delay(voter.uuid, notification_template, extra_vars)


@shared_task
def single_voter_email(voter_uuid, subject_template, body_template, extra_vars={}):
    voter = Voter.objects.get(uuid=voter_uuid)

    the_vars = copy.copy(extra_vars)
    the_vars.update({'election': voter.election})
    the_vars.update({'voter': voter})

    subject = render_template_raw(None, subject_template, the_vars)
    body = render_template_raw(None, body_template, the_vars)

    voter.send_message(subject, body)


@shared_task
def single_voter_notify(voter_uuid, notification_template, extra_vars={}):
    voter = Voter.objects.get(uuid=voter_uuid)

    the_vars = copy.copy(extra_vars)
    the_vars.update({'voter': voter})

    notification = render_template_raw(None, notification_template, the_vars)

    voter.send_notification(notification)


@shared_task
def election_compute_tally(election_id):
    election = Election.objects.get(id=election_id)
    election.compute_tally()

#    election_notify_admin.delay(election_id=election_id,
#                                subject="encrypted tally computed",
#                                body=""""""
    election_notify_all_officers.delay(election_id = election_id,
                                subject = "encrypted tally computed",
                                body = """
The encrypted tally for election %s has been computed.

--
Helios
""" % election.name)

    if election.has_helios_trustee():
        tally_helios_decrypt.delay(election_id=election.id)


@shared_task
def tally_helios_decrypt(election_id):
    election = Election.objects.get(id=election_id)
    election.helios_trustee_decrypt()
#<<<<<<< HEAD
#    election_notify_admin.delay(election_id=election_id,
#                                subject='Helios Decrypt',
#                                body="""
    election_notify_all_officers.delay(election_id = election_id,
                                subject = 'Helios Decrypt',
                                body = """
Helios has decrypted its portion of the tally
for election %s.

--
Helios
""" % election.name)


@shared_task
def voter_file_process(user_id, voter_file_id, v_policy_id = None):
    
    voter_file = VoterFile.objects.get(id = voter_file_id)
    
    
    #start time of voter file processing
    voter_file.start_processing()
    
    registrants = voter_file.registrants()
    
    election = voter_file.election
    user = User.objects.get(id=user_id)
    print("Inside voter file process")
    if v_policy_id:
        v_policy = ValidationPolicy.objects.get(id=v_policy_id)
        for registrant in registrants:
            
            if not ValidationRequest.voter_v_request_exists_by_election(election, registrant.voter_name, registrant.voter_email):
                data = {'old_obj':{},
                        'input':registrant.toJSONDict(),
                        'output':registrant.toJSONDict()}
                
                #prepare data for the validation request creation
                req_data = { 'uuid' : registrant.uuid,
                        'data': data,
                        'action' : Voter.ADD,
                        'modeltype': helios.VOTER,
                        'vp' : v_policy
                      }
                #create the validation request for this registrant
                ValidationRequest.create(user, election, req_data=req_data)
    else:
        print("Inside no validation policy")
        for registrant in registrants:

            if not ValidationRequest.voter_v_request_exists_by_election(election, registrant.voter_name, registrant.voter_email):
                #prepare data for the validation request creation
                data = {'old_obj':{},
                        'input':registrant.toJSONDict(),
                        'output':registrant.toJSONDict()}
                req_data = { 'uuid' : registrant.uuid,
                        'data': data,
                        'action' : Voter.ADD,
                        'modeltype': helios.VOTER,
                        'vp' : None
                      }
                #create the validation request for this registrant
                v_request = ValidationRequest.create(user, election, req_data=req_data)
                registrant.save()
                v_request.commit()
        
        #voter_file.process()
        
    voter_file.end_processing()
    
    election_notify_admin.delay(user_id = user.id, election_id = voter_file.election.id, 
                                subject = 'voter file processed',
                                body = """
Your voter file upload for election %s
has been processed.

%s voters have been created.

--
Helios
""" % (voter_file.election.name, voter_file.num_voters))


@shared_task
def election_notify_admin(user_id, election_id, subject, body):
    #election = Election.objects.get(id = election_id)
    #election.admin.send_message(subject, body)
    user = User.objects.get(id = user_id)
    user.send_message(subject, body)

@shared_task()
def election_notify_all_officers(election_id, subject, body):
    officers = ElectionOfficer.get_by_election_id(election_id)
    
    for officer in officers:
        election_notify_an_officer.delay(officer.id, election_id, subject, body)
    
@shared_task()
def election_notify_an_officer(officer_id, election_id, subject, body):
    officer = ElectionOfficer.objects.filter(id=officer_id)[0]
    officer.user.send_message(subject, body)
