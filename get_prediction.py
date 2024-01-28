import ast

import pandas as pd
from kindwise.plant import PlantApi
from PIL import Image
import requests
from io import BytesIO
from tqdm import tqdm

# Constants
API_KEY = "YOUR API KEY HERE"
TOP_X_PREDICTION = 5


# Function to load image from URL
def load_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img


def get_prediction(row):
    desc_id = row['Desc']
    image_urls = ast.literal_eval(row['Image'])
    url = row['URL']
    location = tuple(map(float, row['Location'].split(',')))
    api = PlantApi(api_key=API_KEY)

    # Creating PIL.Image.Image objects
    images = [load_image(url) for url in image_urls]

    result = api.identify(images, latitude_longitude=location).result.classification

    predictions_line_by_line = []
    predictions_one_line = []

    combined_dict = {"Desc ID": desc_id, "URL": url}
    for i in range(TOP_X_PREDICTION):
        # Check if 'i' is within the range of 'results' length
        if i < len(result.suggestions):
            score = result.suggestions[i].probability
            name = result.suggestions[i].name

            # Further check if there is at least one image in 'images' list
            if result.suggestions[i].similar_images:
                image = result.suggestions[i].similar_images[0].url
            else:
                image = "No image available"
            predictions_line_by_line.append({
                "Desc ID": desc_id,
                "URL": url,
                "Score": score,
                "Name": name,
                "Predic. Img": image
            })
            # Add new keys to the combined dictionary
            combined_dict.update({
                f"Score{i}": score,
                f"Name{i}": name,
                f"Predic. Img{i}": image
            })
        else:
            break  # Break the loop if 'i' is out of range for 'results'

    # Add the combined dictionary to predictions_one_line
    predictions_one_line.append(combined_dict)

    return predictions_line_by_line, predictions_one_line


prediction_per_line = []
one_line_prediction = []
# Read the CSV file
df = pd.read_csv('observation_images.csv')
for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    predictions_line_by_line, predictions_one_line = get_prediction(row)
    prediction_per_line.extend(predictions_line_by_line)
    one_line_prediction.extend(predictions_one_line)

# Convert the list of dictionaries to a DataFrame
df_per_line = pd.DataFrame(prediction_per_line)
df_one_line = pd.DataFrame(one_line_prediction)

df_per_line.to_csv('prediction_per_line.csv', index=False)
df_one_line.to_csv('prediction_one_line_prediction.csv', index=False)
