import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests_oauthlib import OAuth2Session
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout

# OAuth2 Client Setup
oauth = OAuth2Session(client_id=settings.GOOGLE_CLIENT_ID, redirect_uri=settings.GOOGLE_REDIRECT_URI)


def google_login(request):
    oauth = OAuth2Session(
        settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        scope=['profile', 'email']
    )
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        access_type='offline'
    )
    # Save the state to the session
    request.session['oauth_state'] = state
    return redirect(authorization_url)

@csrf_exempt
def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'Authorization code is missing.'}, status=400)

    oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code
    )

    response = oauth.get('https://www.googleapis.com/oauth2/v2/userinfo')
    user_info = response.json()

    # Optionally, you can add logic here to create or update the user in the database

    return JsonResponse({
        'first_name': user_info.get('given_name'),
        'last_name': user_info.get('family_name'),
        'email': user_info.get('email')
    })


@login_required
@csrf_exempt
def get_user_details(request):
    user = request.user
    return JsonResponse({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email
    })

@csrf_exempt
def logout(request):
    auth_logout(request)
    return JsonResponse({'message': 'Successfully logged out.'})