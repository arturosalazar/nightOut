import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests_oauthlib import OAuth2Session
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User ## Import to use Django built in User model so we can save associated users in our DB

# OAuth2 Client Setup
oauth = OAuth2Session(client_id=settings.GOOGLE_CLIENT_ID, redirect_uri=settings.GOOGLE_REDIRECT_URI)


def google_login(request):
    if request.user.is_authenticated:  ## Check if the user is already logged in
        return redirect('http://localhost:5173/Check')  ## If so, redirect to the appropriate page
    
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

    ## Not sure if we need to save token, but added this variable to store result all the same
    token = oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code
    )

    response = oauth.get('https://www.googleapis.com/oauth2/v2/userinfo')
    user_info = response.json()

    # Optionally, you can add logic here to create or update the user in the database
    ## Added logic to create/update user in database
    user, created = User.objects.get_or_create(
        email=user_info['email'],
        defaults={
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
            'username': user_info['email'],
        }
    )

    auth_login(request, user) ## Log the user in using DB stored credentials.
    ## This allows us to store the results without sending JSON to front-end

    return redirect('http://localhost:5173/Check') ## Redirect to desired page after login

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
    request.session.flush()  # Ensure session is cleared
    return JsonResponse({'message': 'Successfully logged out.'})

## Check if user is logged in already or not. Will resposnd accordingly
def check_authentication(request):
    if request.user.is_authenticated:
        return JsonResponse({'is_authenticated': True})
    else:
        return JsonResponse({'is_authenticated': False})