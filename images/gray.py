from PIL import Image
import os

def greyscale_images_in_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"The folder {folder_path} does not exist.")
        return

    # Loop through all files in the folder
    for filename in os.listdir(folder_path):
        # Construct the full file path
        file_path = os.path.join(folder_path, filename)

        # Check if the file is an image
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
            # Open the image
            with Image.open(file_path) as img:
                # Convert the image to greyscale
                greyscale_img = img.convert('L')
                # Save the greyscale image
                greyscale_img.save(file_path)
                print(f"Converted {filename} to greyscale.")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing images: ")
    greyscale_images_in_folder(folder_path)
