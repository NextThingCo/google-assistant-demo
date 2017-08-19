# Setup

To enable access to the Google Assistant API, do the following on your development machine:

1. In the Cloud Platform Console, go to the [Projects page](https://console.cloud.google.com/project?pli=1). Select an existing project or create a new project.

2. Enable the Google Assistant API on the project you selected [at this link](https://console.developers.google.com/apis/api/embeddedassistant.googleapis.com/overview?pli=1). Select your project as mentioned in step 1 and click the “Enable” button.

3. Create an OAuth Client ID with the following steps:
    - [Create the client ID at this link.](https://console.developers.google.com/apis/credentials/oauthclient)
    - You may need to set a product name for the product consent screen. On the OAuth consent screen tab, give the product a name and click Save.
    - Click Other and give the client ID a name.
    - Click Create. A dialog box appears that shows you a client ID and secret. (No need to remember or save this, just close the dialog.)
    - Click ⬇ (at the far right of screen) for the client ID to download the client secret JSON file (client_secret_XXXX.json).

4. Copy the client_secret_XXXX.json file to this folder.

5. Download GadgetOS to your development machine and build the OS. Flash the image to your CHIP Pro.
 
6. [Download the GadgetCLI tools.](https://docs.getchip.com/gadget.html#set-up-gadget)

7. [Setup the wifi on your CHIP Pro.](https://docs.getchip.com/gadget.html#set-up-wifi)

8. Do a "gadget build" from this folder and then "gadget deploy" and "gadget start"

9. With CHIP Pro connected to your computer, follow the instructions through the terminal to finish authentication.
