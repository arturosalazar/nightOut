import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def search_businesses(request):
    location = request.data.get('location')
    business_type = request.data.get('business_type')

    # Google Places API endpoint for text search
    google_places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    # Parameters for the text search request
    params = {
        'query': f"{business_type} in {location}",
        'key': settings.GOOGLE_PLACES_API_KEY,
    }

    response = requests.get(google_places_url, params=params)
    data = response.json()

    # Extract top 10 results
    top_results = data.get('results', [])[:10]

    results = []
    for result in top_results:
        place_id = result.get('place_id')

        # Perform a Place Details search for each place
        if place_id:
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                'place_id': place_id,
                'fields': 'name,formatted_address,rating,formatted_phone_number,opening_hours,photos',
                'key': settings.GOOGLE_PLACES_API_KEY,
            }
            details_response = requests.get(details_url, params=details_params)
            details_data = details_response.json().get('result', {})

            # Get the photo_reference from the photos array
            photo_reference = None
            if 'photos' in details_data and len(details_data['photos']) > 0:
                photo_reference = details_data['photos'][0].get('photo_reference')

            # If a photo_reference is found, get the photo URL
            photo_url = None
            if photo_reference:
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={settings.GOOGLE_PLACES_API_KEY}"

            result_data = {
                'name': details_data.get('name'),
                'address': details_data.get('formatted_address'),
                'rating': details_data.get('rating'),
                'phone_number': details_data.get('formatted_phone_number'),
                'opening_hours': details_data.get('opening_hours', {}).get('weekday_text'),
                'photo_url': photo_url,  # Include the photo URL
            }
            results.append(result_data)

    return Response(results)
