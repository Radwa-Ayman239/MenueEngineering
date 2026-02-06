# This directory contains trained ML models
# Do not commit large model files to git - use Git LFS or model registry instead

# Required files:
# - menu_classifier.joblib   (Decision Tree model from notebook)
# - label_encoder.joblib     (Label encoder for category names)

# To generate these files, run the following in your notebook:
#
# import joblib
# joblib.dump(model, "models/menu_classifier.joblib")
# joblib.dump(label_encoder, "models/label_encoder.joblib")
