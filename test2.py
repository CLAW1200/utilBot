import requests
from PIL import Image
import hashlib
def add_speech_bubble(image_link, speech_bubble_y_scale=0.2):
    """
    Add a speech bubble to the top of the image or each frame of a GIF.
    """
    data = requests.get(image_link).content
    speechBubble = Image.open("assets/speechBubble.png").convert("RGBA")
    image_seed = hashlib.md5(requests.get(image_link).content).hexdigest()
    output_path = f"temp/speech_bubble_output{image_seed}.gif"

    # save the image to a file
    with open("newimagedownload.png", 'wb') as f:
        f.write(data) 

    # Load both images
    image = Image.open("newimagedownload.png").convert("RGBA")
    bubble = Image.open(speechBubble).convert("RGBA")

    # Calculate 20% of the height of the first image
    new_height = int(image.height * speech_bubble_y_scale)

    # Resize the speech bubble to exactly 20% of the image's height and 100% of the image's width
    bubble = bubble.resize((image.width, new_height))

    # Create a new image with the same size as the original image
    result = Image.new("RGBA", image.size)

    # Paste the resized speech bubble onto the new image at the top left corner (0,0)
    result.paste(bubble, (0,0), bubble)

    # Iterate over each pixel in the images
    for x in range(image.width):
        for y in range(image.height):
            # Get the current pixel
            pixel_image = image.getpixel((x, y))
            pixel_result = result.getpixel((x, y))

            # If the pixel in the result image is not completely transparent
            if pixel_result[3] > 0:  # Alpha value is not 0
                # Make the corresponding pixel in the first image completely transparent
                result.putpixel((x, y), (pixel_image[0], pixel_image[1], pixel_image[2], 0))
            else:
                # Otherwise, keep the original pixel
                result.putpixel((x, y), pixel_image)

    # Save the result
    image.close()
    bubble.close()
    result.save(output_path, "GIF")
    return output_path

if __name__ == "__main__":
    print (add_speech_bubble("https://cdn.discordapp.com/attachments/1109190675720851578/1184906860998971493/image.png?ex=658dad82&is=657b3882&hm=87a933c48cf01450df6a75dcaa2ec98b98739b7c394f413171513cc1d10b8c18&", 0.2))
