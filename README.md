# SpotDash

## Description

SpotDash is a web application built using Flask that simplifies the frustration of finding parking lots near you. It consists of three main modules: User, Managers, and Admin.

- **User Module:** Users can create an account and log in to access the user page, where they can find a list of parking lots within a specific radius of their location.

- **Managers Module:** Parking area owners can create accounts as managers. They can upload images of their parking areas and use Mask R-CNN to detect available parking spaces. Additionally, managers can detect space availability from video using OpenCV.

- **Admin Module:** The admin has control over verifying manager accounts and manages user accounts.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

## Installation

To run SpotDash locally, make sure you have the following dependencies installed:

- Python 3.7
- TensorFlow
- Keras
- Mask R-CNN (Refer to [Mask R-CNN GitHub Repo](https://github.com/matterport/Mask_RCNN))
- OpenCV
- Streamlit
- Flask
- TailwindCSS
- Sqlite3 (Database)

For enhanced performance (GPU support), use `tensorflow-gpu` if you have a compatible GPU.

### Download Mask R-CNN Model

Download the Mask R-CNN model from [this link](https://github.com/matterport/Mask_RCNN/releases/download/v2.0/mask_rcnn_coco.h5) and place it in the appropriate directory.

## Usage

" flask run " (to run flask application[users and managers])
" streamlit run app.py " (to run streamlit application[Admin only])

## Features

SpotDash offers the following key features:

- User Module:
  - Create an account and log in.
  - Get a list of parking lots within a specific radius.
  - View parking areas on the main page map.
  - Filter the map to scale up to 10km radius.
  - Select a parking area to view available and occupied spaces.
  - Obtain Google Maps directions to selected parking areas.
  - *(Add any additional features specific to the User module)*

- Managers Module:
  - Create an account as a parking area manager.
  - Account activation after admin verification and approval.
  - Log in and add parking details.
  - Upload images of parking areas to detect available parking spaces.
  - Detect occupied spaces (car, motorcycle, or truck) from images.
  - Update parking space status for users to see.
  - Manually mark spaces in videos for detection and update.
  - *(Add any additional features specific to the Managers module)*

- Admin Module:
  - Use Streamlit to manage admin and manager accounts.
  - Approve manager accounts for activation.
  - Get a visualized view of user data.
  - *(Add any additional features specific to the Admin module)*


## License

SpotDash is open-source and released under the [MIT License](LICENSE.md).

## Contact

For any questions, suggestions, or feedback, feel free to contact on LinkedIn: [Manukrishna T M](https://www.linkedin.com/in/manukrishna-t-m).

## Acknowledgments

We would like to thank the following individuals/organizations for their contributions and inspiration:

- [Mask R-CNN](https://github.com/matterport/Mask_RCNN) for their amazing work on the Mask R-CNN model.
- This article by [Ageitgey](https://medium.com/@ageitgey/snagging-parking-spaces-with-mask-r-cnn-and-python-955f2231c400) for valuable insights on parking space detection.



