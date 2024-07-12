import sys
import os

root_path = os.path.dirname(os.path.abspath(__file__))
docgeonet_path = os.path.join(root_path, 'DocGeoNet')

sys.path.append(docgeonet_path)

from DocGeoNet.inference import operationNet

def process_image(image_path):


    result = operationNet(image_path)
    print("process_image")
    print(result)
    return result

