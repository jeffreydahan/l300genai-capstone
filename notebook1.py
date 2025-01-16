import os
import time
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
  generation_config=generation_config,
)

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
  upload_to_gemini("75871108003__8F64C39E-71CA-4BE1-BD10-5D941005C43B.MOV", mime_type="video/quicktime"),
  upload_to_gemini("75871118579__59F841E6-DDCE-4FFF-ABF3-85771274BF78.MOV", mime_type="video/quicktime"),
]

# Some files have a processing delay. Wait for them to be ready.
wait_for_files_active(files)

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        files[0],
        files[1],
      ],
    },
    {
      "role": "user",
      "parts": [
        "Please compare these two paper bags. One video shows the before and the other video shows the after. Please list out in bullet points any damage you see and on what part of the bag. Also say if it is minor damage (like a scratch or discoloring) or if major damage (like ripping or broken parts). ",
      ],
    },
    {
      "role": "model",
      "parts": [
        "Okay, I can help with that. Here’s a comparison of the two paper bags based on the video you provided:\n\n**Before:**\n\n*   The bag appears to be mostly in good condition, with no visible major damage or rips to its structure\n*  There is an order tag attached to the bag, which has “Order #” and “Bag” on the tag.\n*   The bag is brown paper with white printing. One side has the logo of “Wolt market” on the center of the bag.\n*   The other side has a large reindeer drawing on it, as well as an order tag with “Order #” and “Bag” written on the tag.\n\n**After:**\n\n*   The bag has a tear on the left-hand side where the handles attach to the bag, and is now open. This is major damage.\n* There is a red mark drawn on the Wolt market side of the bag. This is minor damage.\n* The bag is now open and is no longer laying flat on the table.\n* The bag has a tear on the bottom fold of the bag. This is minor damage.\n\nOverall, the first bag shows little to no damage while the second video shows several small rips to the bag and a tear on the side, which appears to be more of a major tear.",
      ],
    },
  ]
)

response = chat_session.send_message("INSERT_INPUT_HERE")

print(response.text)
