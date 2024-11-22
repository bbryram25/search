from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)

app = Flask(__name__)

es = Elasticsearch(
    "https://127.0.0.1:9200",
    basic_auth=('elastic', 'Bam352024647'), 
    verify_certs=False
)

def search_recipes(query_text, page=1, size=20):
    """Search for recipes in Elasticsearch based on title or ingredient and filter duplicates by title."""
    query = {
        "query": {
            "bool": {
                "should": [
                {"match": {"ingredients.name": {"query": query_text, "fuzziness": "AUTO"}}},  # Fuzzy match in ingredients
                {"match": {"title": {"query": query_text, "fuzziness": "AUTO", "boost": 5}}},  # Fuzzy match in title with boost
                {"match_phrase_prefix": {"ingredients.name": {"query": query_text}}},  # Partial match in ingredients
                {"match_phrase_prefix": {"title": {"query": query_text, "boost": 5}}}  # Partial match in title with boost
                ],
                "minimum_should_match": 1  
            }
        },
        "from": (page - 1) * size,  
        "size": size  
    }

    # Perform the search
    response = es.search(index='recipedessert', body=query) 
    print("Elasticsearch Response:", response)
    
    recipes = []
    seen_titles = set()  # Track duplicate recipes by title
    for hit in response['hits']['hits']:
        recipe = hit['_source']
        
        # Check if the recipe title has already been seen
        if recipe['title'] not in seen_titles:
            recipes.append({
                'title': recipe['title'],
                'description': recipe.get('description', 'No description available.'),
                'preparation_time': recipe.get('preparation_time_minutes', 'N/A'),
                'cooking_time': recipe.get('cooking_time_minutes', 'N/A'),
                'ratings': recipe.get('ratings', 'N/A'),
                'ingredients': recipe.get('ingredients', []),
                'steps': recipe.get('steps', []),
                'created': recipe.get('created', 'N/A'),
                'image_url': recipe.get('image_url', 'default_image_url'), 
                'score': hit['_score']
            })
            seen_titles.add(recipe['title'])
    
    # Pagination metadata
    total_results = response['hits']['total']['value']
    has_more_pages = (page * size) < total_results
    
    # Return recipes with pagination metadata
    return {
        "total_results": total_results,
        "page": page,
        "page_size": size,
        "has_more_pages": has_more_pages,
        "recipes": recipes
    }
   

@app.route('/')
def index():
    return render_template('searchpage.html')


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query_text = data.get('query_text')  # Accepting 'query_text' instead of 'ingredient'
    page = data.get('page', 1) 
    size = data.get('size', 20)  
    
    # Passing 'query_text', 'page', and 'size' to the search_recipes function
    search_results = search_recipes(query_text, page=page, size=size)
    
    return jsonify(search_results)


@app.route('/TeamPage')
def teampage():
    return render_template('teampage.html')

@app.route('/searchpage')
def searchpage():
    return render_template('searchpage.html')

if __name__ == "__main__":
    app.run(debug=True, port=5005)
