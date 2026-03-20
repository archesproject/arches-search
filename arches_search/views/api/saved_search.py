from django.db.models import Q

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.models.models import (
    SavedSearch,
    SharedSearchXUser,
    SharedSearchXGroup,
)


def _serialize_saved_search(saved_search, include_created_at=True):
    data = {
        "savedsearchid": str(saved_search.savedsearchid),
        "name": saved_search.name,
        "description": saved_search.description,
        "query_definition": saved_search.query_definition,
        "creator": {
            "id": saved_search.creator_id,
            "username": saved_search.creator.username,
        },
    }
    if include_created_at:
        data["created_at"] = saved_search.created_at.isoformat()
    return data


class SavedSearchAPI(APIBase):
    def get(self, request):
        scope = request.GET.get("scope", "mine")
        search = request.GET.get("search", "")

        if scope == "mine":
            saved_searches = SavedSearch.objects.filter(creator=request.user)

        else:  # if not mine, get all shared searches
            user_shared = SavedSearch.objects.filter(shared_users__user=request.user)
            group_shared = SavedSearch.objects.filter(
                shared_groups__group__in=request.user.groups.all()
            )
            saved_searches = (
                (user_shared | group_shared).exclude(creator=request.user).distinct()
            )

        if search:
            saved_searches = saved_searches.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        saved_searches = saved_searches.select_related("creator").order_by("name")

        return JSONResponse([_serialize_saved_search(s) for s in saved_searches])

    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        name = body.get("name", "").strip()
        if not name:
            return JSONResponse({"error": "name is required"}, status=400)

        query_definition = body.get("query_definition")
        if query_definition is None:
            return JSONResponse({"error": "query_definition is required"}, status=400)

        saved_search = SavedSearch.objects.create(
            name=name,
            description=body.get("description", ""),
            query_definition=query_definition,
            creator=request.user,
        )

        SharedSearchXUser.objects.bulk_create(
            [
                SharedSearchXUser(saved_search=saved_search, user_id=uid)
                for uid in body.get("users", [])
            ]
        )

        SharedSearchXGroup.objects.bulk_create(
            [
                SharedSearchXGroup(saved_search=saved_search, group_id=gid)
                for gid in body.get("groups", [])
            ]
        )

        return JSONResponse(
            _serialize_saved_search(saved_search, include_created_at=False), status=201
        )

    def delete(self, request, savedsearchid):
        try:
            saved_search = SavedSearch.objects.get(
                savedsearchid=savedsearchid,
                creator=request.user,
            )
        except SavedSearch.DoesNotExist:
            return JSONResponse(status=404)

        saved_search.delete()
        return JSONResponse(status=204)
