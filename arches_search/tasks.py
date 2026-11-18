from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from arches.app.tasks import create_user_task_record, notify_completion


@shared_task(bind=True)
def create_resource_set_from_search(self, userid, name, description, search_body):
    from arches_search.views.api.resource_sets import save_search_as_resource_set

    create_user_task_record(self.request.id, self.name, userid)
    user = get_user_model().objects.get(pk=userid)
    try:
        message = save_search_as_resource_set(
            user, name, description, search_body, in_background=True
        )["message"]
    except ValidationError as error:
        # Results changed before the task ran; tell the user why.
        message = " ".join(error.messages)
    notify_completion(message, user)
    # No notiftype_name: the notification above is the only one; the link
    # callback (update_user_task_record) just marks the task done.
    return {"taskid": self.request.id, "msg": message}
