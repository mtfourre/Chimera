from models import User, Post, UserLogin, Consumer, Chef, Location, Billing, Album, ProfilePhoto, Blob, Order
from django.http import HttpResponse
from .settings import PROTOCOL
from datetime import datetime
from json import dumps, loads
import urllib2
import jobs


# home

# /
def home(request):  # /
    response = dumps(
        {'message': 'This is the MealSloth API. If you would like to learn more about MealSloth, please visit the URL',
         'url': 'mealsloth.com', }
    )
    return HttpResponse(response, content_type='application/json')


# blob

# /blob/bucket
def blob_bucket_url(request):  # /blob/bucket/url
    if request.method == 'POST':
        return HttpResponse(
            urllib2.urlopen(PROTOCOL + 'blob.mealsloth.com/bucket/url/'),
            content_type='application/json'
        )
    else:
        response = dumps({'result': 9001, 'message': 'Method only accessible by POST'})
        return HttpResponse(response, content_type='application/json')


# /blob/upload
def blob_upload(request):  # /blob/upload
    if request.method == 'POST':
        body = loads(request.body)
        image_file = body.get('file')
        dictionary = {'file': image_file}
        if body.get('album_id'):
            dictionary['album_id'] = body.get('album_id')
        data = dumps(dictionary)
        re = urllib2.urlopen(PROTOCOL + 'blob.mealsloth.com/blob/image/upload/', data)
        return HttpResponse(re)
    else:
        response = dumps({'result': 9001, 'message': 'Method only accessible by POST'})
        return HttpResponse(response, content_type='application/json')


# blob/view
def blob_view(request):  # /blob/view
    if request.method == 'POST':
        if not request.POST['blob_id']:
            response = dumps({'result': 9000, 'message': 'Missing parameter blob_id'})
            return HttpResponse(response)
        blob_id = request.POST['blob_id']
        blob = Blob.objects.get(pk=blob_id)
        if not blob:
            response = dumps({'result': 9004, 'message': 'Item not in database'})
            return HttpResponse(response)
        response = dumps({'url': '', 'result': 1000})  # TODO: Include a real URL
        return HttpResponse(response)
    else:
        response = dumps({'result': 9001, 'message': 'Method only accessible by POST'})
        return HttpResponse(response)


# blog

# /blog/upload
def blog_image_upload(request):  # /blog/image/upload
    if request.method == 'POST':
        body = loads(request.body)
        image_file = body['file']
        data = dumps({'file': image_file, 'album_id': body['album_id']})
        try:
            re = urllib2.urlopen(PROTOCOL + 'blob.mealsloth.com/blog/image/upload/', data)
            return HttpResponse(re, content_type='application/json')
        except urllib2.HTTPError:
            response = {'result': 2040, 'message': 'Error from Hydra'}
            return HttpResponse(response, content_type='application/json')
    else:
        response = dumps({'result': 9000, 'message': 'Only accessible with POST'})
        return HttpResponse(response, content_type='application/json')


# user

# /user
def user(request):  # /user
    if request.method == 'POST':
        body = loads(request.body)
        email = body.get('email')
        user_id = body.get('user_id')
        if email:
            user = User.objects.filter(email=email).values()
            if user.count() > 0:
                response = dumps({'user': user[0], 'result': 1000})
                return HttpResponse(response, content_type='application/json')
            else:
                response = dumps({'result': 9000, 'message': 'Invalid parameter'})
                return HttpResponse(response, content_type='application/json')
        elif user_id:
            user = User.objects.filter(pk=user_id)
            if user.count() > 0:
                response = dumps({'user': user[0], 'result': 1000})
                return HttpResponse(response, content_type='application/json')
        else:
            response = {'result': 9000, 'message': 'Invalid parameter'}
            return HttpResponse(dumps(response), content_type='application/json')
    else:
        return HttpResponse(dumps({'result': 9001, 'message': 'This method is accessible only by POST'}))


# /user/create
def user_create(request):  # /user/create
    if request.method == 'POST':
        if not request.body:
            response = {'result': 9000, 'message': 'Invalid parameter'}
            return HttpResponse(dumps(response), content_type='application/json')

        json_request = loads(request.body)

        if not json_request.get('email') and json_request.get('password'):
            response = {'result': 9000, 'message': 'Invalid parameter'}
            return HttpResponse(dumps(response), content_type='application/json')

        current_user = User(
            email=json_request.get('email'),
            join_date=datetime.utcnow(),
        )

        if User.objects.filter(email=current_user.email):
            response = {'result': 2000, 'message': 'Email address already in use'}
            return HttpResponse(dumps(response), content_type='application/json')
        else:
            current_user.save()

        current_user_login = UserLogin(
            id=current_user.user_login_id,
            user_id=current_user.id,
            username=current_user.email,
            password=json_request.get('password'),
        )

        current_user_login.save()

        if not UserLogin.objects.filter(id=current_user_login.id):
            current_user.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        location = Location(
            id=current_user.location_id,
            user_id=current_user.id,
        )

        location.save()

        if not Location.objects.filter(id=location.id):
            current_user.delete()
            current_user_login.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        consumer = Consumer(
            id=current_user.consumer_id,
            user_id=current_user.id,
            location_id=location.id,
        )

        consumer.save()

        if not Consumer.objects.filter(id=consumer.id):
            current_user.delete()
            current_user_login.delete()
            location.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        chef = Chef(
            id=current_user.chef_id,
            user_id=current_user.id,
            location_id=location.id,
        )

        chef.save()

        if not Chef.objects.filter(id=chef.id):
            current_user.delete()
            current_user_login.delete()
            location.delete()
            consumer.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        billing = Billing(
            id=current_user.billing_id,
            user_id=current_user.id,
            consumer_id=consumer.id,
            chef_id=chef.id,
            location_id=location.id,
        )

        billing.save()

        if not Billing.objects.filter(id=billing.id):
            current_user.delete()
            current_user_login.delete()
            consumer.delete()
            chef.delete()
            location.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        album = Album()

        album.save()

        if not Album.objects.filter(id=album.id):
            current_user.delete()
            current_user_login.delete()
            consumer.delete()
            chef.delete()
            location.delete()
            billing.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        profile_photo = ProfilePhoto(
            id=current_user.profile_photo_id,
            album_id=album.id,
            user_id=current_user.id,
        )

        profile_photo.save()

        if not ProfilePhoto.objects.filter(id=profile_photo.id):
            current_user.delete()
            current_user_login.delete()
            consumer.delete()
            chef.delete()
            location.delete()
            billing.delete()
            album.delete()
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        current_user = User.objects.get(pk=current_user.id)
        current_user_login = UserLogin.objects.get(pk=current_user_login.id)

        if not current_user and current_user_login:
            response = {'result': 9010, 'message': 'Could not save to database'}
            return HttpResponse(dumps(response), content_type='application/json')

        current_user = User.objects.filter(id=current_user.id).values()[0]
        current_user_login = UserLogin.objects.filter(id=current_user_login.id).values()[0]

        response = {'user': current_user, 'user_login': current_user_login, 'result': 1000}
        return HttpResponse(dumps(response), content_type='application/json')
    else:
        response = {'result': 9001, 'message': 'This method is accessible only by POST'}
        return HttpResponse(dumps(response), content_type='application/json')


# post

# /post
def post(request):  # /post
    if request.method == 'POST':
        body = loads(request.body)
        try:
            post_id = body['post_id']
        except KeyError:
            response = {'result': 9000, 'message': 'Invalid parameter'}
            return HttpResponse(dumps(response), content_type='application/json')
        if Post.objects.filter(id=post_id).values().count() > 0:
            post = Post.objects.filter(id=post_id).values()[0]
            response = post
            response['result'] = 1000
            return HttpResponse(dumps(response), content_type='application/json')
        else:
            response = {'result': 9000, 'message': 'Invalid parameter'}
            return HttpResponse(dumps(response), content_type='application/json')
    else:
        response = {'result': 9001, 'message': 'This method is accessible only by POST'}
        return HttpResponse(dumps(response), content_type='application/json')


# user-login

# /user-login
def user_login(request):  # /user-login
    if request.method == 'POST':
        body = loads(request.body)
        user_login_id = body.get('user_login_id')
        user_id = body.get('user_id')
        if user_login_id:
            if UserLogin.objects.filter(id=user_login_id).values().count() > 0:
                current_user_login = UserLogin.objects.filter(id=user_login_id).values()[0]
                response = {'user_login': current_user_login, 'result': 1000}
                return HttpResponse(dumps(response), content_type='application/json')
        elif user_id:
            if UserLogin.objects.filter(user_id=user_id).values().count() > 0:
                current_user_login = UserLogin.objects.filter(user_id=user_id).values()[0]
                response = {'user_login': current_user_login, 'result': 1000}
                return HttpResponse(dumps(response), content_type='application/json')
        else:
            response = {'result': 9000, 'message': 'Invalid parameter'}
            return HttpResponse(dumps(response), content_type='application/json')
    else:
        response = {'result': 9001, 'message': 'This method is accessible only by POST'}
        return HttpResponse(dumps(response), content_type='application/json')


# job

# /job/post
def job_post_status(request):  # /job/post/status
    return jobs.job_post_status()


# /job/order
def job_order_status(request):  # /job/order/status
    return jobs.job_order_status()
