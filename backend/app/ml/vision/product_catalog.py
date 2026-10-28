"""Recognition vocabulary for the pretrained CLIP image/text model.

These are candidate descriptions, not training examples or brand lookup rules.
"""

FOODS = {
    "Produce": ["apple", "banana", "orange", "lemon", "lime", "mango", "grapes", "strawberries", "watermelon", "pineapple", "papaya", "pear", "peach", "avocado", "kiwi", "pomegranate", "tomato", "potato", "onion", "carrot", "cucumber", "broccoli", "cauliflower", "cabbage", "lettuce", "spinach", "bell pepper", "eggplant", "mushrooms", "garlic", "ginger", "green beans", "peas", "corn"],
    "Dairy": ["milk", "yogurt", "cheese", "butter", "paneer", "cream", "ghee"],
    "Eggs": ["eggs"],
    "Bread & bakery": ["bread", "bread rolls", "croissant", "cake", "doughnut", "chapati flatbread"],
    "Meat & poultry": ["raw chicken", "raw beef", "raw pork", "raw lamb", "sausages"],
    "Seafood": ["raw fish", "shrimp", "crab"],
    "Grains & pulses": ["rice", "wheat flour", "oats", "lentils", "dried beans", "pasta", "chickpeas"],
    "Prepared food": ["cooked rice", "biryani", "curry", "dal lentil soup", "pizza", "burger", "sandwich", "salad", "noodles", "sushi", "idli", "dosa", "samosa"],
    "Snacks & confectionery": ["potato chips", "biscuits", "chocolate", "candy", "nuts", "popcorn"],
    "Beverages": ["orange juice", "fruit juice", "bottled water", "coffee", "tea", "energy drink"],
    "Frozen food": ["ice cream", "frozen vegetables", "frozen meal"],
    "Canned goods": ["canned beans", "canned soup", "canned corn"],
    "Canned fish": ["canned tuna", "canned sardines"],
    "Condiments & oils": ["cooking oil", "ketchup", "jam", "honey", "peanut butter"],
}

CANDIDATES = [
    {"name": name.capitalize(), "category": category, "prompt": f"a photo of {name}, a food or drink"}
    for category, names in FOODS.items() for name in names
] + [
    {"name": "Cola soft drink", "category": "Beverages", "prompt": "a photo of a can or bottle of cola soda, Coca-Cola or Pepsi soft drink"},
    {"name": "Packaged food · contents not visible", "category": "Packaged food", "prompt": "a close up photo of a sealed metal food can lid with a printed date stamp"},
] + [
    {"name": "No food visible", "category": None, "prompt": prompt}
    for prompt in ["a photo of a person", "a photo of a dog or cat", "a photo of a document with printed text", "a photo of an empty blank background", "a photo of an electronic device", "a photo of a household object that is not food"]
]

PACKAGING = ["aluminum drink can", "plastic drink bottle", "glass bottle", "food carton", "metal food tin", "close-up of a metal food can lid", "food jar", "plastic food bag", "food box", "food on a plate", "unpackaged fruit or vegetables"]
