# utils/ai_models.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import numpy as np
import os

# Define a directory to save/load models
MODEL_SAVE_DIR = "data/models"
os.makedirs(MODEL_SAVE_DIR, exist_ok=True)

def build_and_train_cnn(input_shape, num_classes, X_train, y_train, X_test, y_test, epochs=10, batch_size=32):
    """
    Builds, compiles, and trains a simple 1D CNN model.
    Assumes input_shape is (timesteps, features) for 1D CNN.
    For image data, input_shape would be (height, width, channels) and you'd use Conv2D.
    """
    model = Sequential()
    model.add(Conv1D(filters=64, kernel_size=2, activation='relu', input_shape=input_shape))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.2))
    model.add(Flatten())
    model.add(Dense(100, activation='relu'))
    model.add(Dropout(0.2))

    if num_classes > 1:
        model.add(Dense(num_classes, activation='softmax'))
        loss_fn = 'sparse_categorical_crossentropy' # For integer labels
        metrics = ['accuracy']
    else: # Binary classification or regression
        model.add(Dense(1, activation='sigmoid')) # For binary classification
        loss_fn = 'binary_crossentropy'
        metrics = ['accuracy']
        # For regression, use Dense(1, activation='linear') and loss_fn='mse'

    model.compile(optimizer=Adam(learning_rate=0.001), loss=loss_fn, metrics=metrics)

    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_test, y_test),
        verbose=0 # Suppress verbose output for Streamlit
    )
    return model, history

def predict_with_cnn(model, X_data):
    """Makes predictions using the trained CNN model."""
    predictions = model.predict(X_data)
    return predictions

def save_model(model, name):
    """Saves the trained Keras model."""
    path = os.path.join(MODEL_SAVE_DIR, f"{name}.h5")
    model.save(path)
    return path

def load_model(name):
    """Loads a Keras model."""
    path = os.path.join(MODEL_SAVE_DIR, f"{name}.h5")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    model = tf.keras.models.load_model(path)
    return model

# Example for image data preprocessing (conceptual, not directly used in current ai_model.py)
# def preprocess_image_data(df, image_path_col, target_size=(64, 64)):
#     """
#     Loads and preprocesses images from paths in a DataFrame for CNN.
#     Requires 'opencv-python' or 'Pillow'.
#     """
#     images = []
#     labels = []
#     for idx, row in df.iterrows():
#         img_path = row[image_path_col]
#         label = row['target_label_column'] # Replace with your actual label column
#         try:
#             img = tf.keras.preprocessing.image.load_img(img_path, target_size=target_size)
#             img_array = tf.keras.preprocessing.image.img_to_array(img)
#             img_array = img_array / 255.0 # Normalize
#             images.append(img_array)
#             labels.append(label)
#         except Exception as e:
#             print(f"Could not load image {img_path}: {e}")
#             continue
#     return np.array(images), np.array(labels)