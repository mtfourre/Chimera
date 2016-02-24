from Chimera.view.album.view_album_create import album_create as create_album
from datetime import datetime, timedelta
from Chimera.utils import model_to_dict
from Chimera.models import Post, Chef
from django.http import HttpResponse
from Chimera.results import Result
from json import loads, dumps


def post_create(request, **kwargs):
    if (request and request.method == 'POST') or kwargs:
        if request and request.method == 'POST':
            body = loads(request.body)
        elif kwargs:
            body = kwargs
        else:
            response = Result.get_result_dump(Result.INVALID_PARAMETER)
            return HttpResponse(response, content_type='application/json')

        chef_id = body.get('chef_id')
        name = body.get('name')
        description = body.get('description')
        capacity = body.get('capacity')

        if not chef_id and name and description and capacity:
            response = Result.get_result_dump(Result.INVALID_PARAMETER)
            return HttpResponse(response, content_type='application/json')

        try:
            chef = Chef.objects.get(pk=chef_id)
        except Chef.DoesNotExist:
            response = Result.get_result_dump(Result.DATABASE_ENTRY_NOT_FOUND)
            return HttpResponse(response, content_type='application/json')
        except Chef.MultipleObjectsReturned:
            response = Result.get_result_dump(Result.DATABASE_MULTIPLE_ENTRIES)
            return HttpResponse(response, content_type='application/json')

        album_create_kwargs = {'Please': 'Thank you', }  # Junk args sent to pass kwargs null check
        album = create_album(request=None, **album_create_kwargs)

        post = Post(
            chef_id=chef.id,
            location_id=chef.location_id,
            name=name,
            description=description,
            album_id=album.id,
            capacity=capacity,
            post_time=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            expire_time=(datetime.utcnow() + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
        )

        try:
            post.save()
        except StandardError:
            album.delete()
            response = Result.get_result_dump(Result.DATABASE_CANNOT_SAVE_POST)
            return HttpResponse(response, content_type='application/json')

        if kwargs:
            return post

        response = {'post': model_to_dict(post)}
        Result.append_result(response, Result.SUCCESS)
        response = dumps(response)
        return HttpResponse(response, content_type='application/json')
    else:
        response = Result.get_result_dump(Result.POST_ONLY)
        return HttpResponse(response, content_type='application/json')
