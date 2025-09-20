# pages/ai_model.py
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from utils.ai_models import (
    build_and_train_cnn,
    predict_with_cnn,
    save_model,
    load_model,
)  # Assuming these functions
import os


def show_page():
    st.header("🧠 Step 8: AI Model Training & Inference")
    st.info(
        "Train a Convolutional Neural Network (CNN) model on your data and make predictions."
    )

    if st.session_state.clean_df.empty:
        st.warning("No data loaded. Please go back to Step 1: Data Import.")
        return

    df = st.session_state.clean_df.copy()

    # --- Model Configuration ---
    st.subheader("⚙️ Model Configuration")

    # Assuming a classification task for simplicity.
    # For image data, you'd need paths to images in your DataFrame.
    # For tabular data, you'd need to convert it to a suitable format (e.g., 1D CNN, or treat as images).
    # This example assumes a simple tabular classification.

    all_columns = df.columns.tolist()
    feature_cols = st.multiselect(
        "Select Feature Columns (X)",
        options=all_columns,
        default=[col for col in all_columns if df[col].dtype in ["int64", "float64"]],
    )
    target_col = st.selectbox(
        "Select Target Column (y)",
        options=[col for col in all_columns if col not in feature_cols],
    )

    if not feature_cols or not target_col:
        st.warning("Please select feature and target columns to proceed.")
        return

    # Basic data preparation for a generic CNN (e.g., tabular data treated as sequences)
    try:
        X = df[feature_cols].values
        y = df[target_col].values

        # Encode target if categorical
        if (
            df[target_col].dtype == "object" or df[target_col].nunique() < 20
        ):  # Heuristic for categorical
            le = LabelEncoder()
            y = le.fit_transform(y)
            st.session_state.label_encoder = le  # Store for inverse transform later
            num_classes = len(le.classes_)
        else:
            num_classes = (
                1  # For regression or binary classification without explicit encoding
            )

        # Reshape X for a simple 1D CNN (assuming each row is a sequence)
        # This is a very basic assumption; real CNNs for tabular data are more complex.
        # For image data, X would be an array of image data.
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)  # Ensure 2D for feature processing
        X = X.reshape(X.shape[0], X.shape[1], 1)  # Add a channel dimension for 1D CNN

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        st.write(f"Features shape: {X.shape}")
        st.write(f"Target shape: {y.shape}")
        st.write(
            f"Training samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}"
        )

    except Exception as e:
        st.error(
            f"Error preparing data: {e}. Ensure selected columns are numeric or can be encoded."
        )
        return

    # Model Parameters
    epochs = st.slider("Epochs", min_value=1, max_value=50, value=10)
    batch_size = st.slider("Batch Size", min_value=16, max_value=256, value=32)

    # --- Train Model ---
    st.subheader("🚀 Train Model")
    if st.button("Start Training", type="primary"):
        if X_train.shape[0] == 0 or X_test.shape[0] == 0:
            st.error(
                "Not enough data to train. Please check your feature/target selection or data import."
            )
            return

        with st.spinner("Training CNN model... This may take a while."):
            try:
                model, history = build_and_train_cnn(
                    input_shape=X_train.shape[1:],
                    num_classes=num_classes,
                    X_train=X_train,
                    y_train=y_train,
                    X_test=X_test,
                    y_test=y_test,
                    epochs=epochs,
                    batch_size=batch_size,
                )
                st.session_state.trained_model = model
                st.success("✅ Model training complete!")

                st.subheader("Training History")
                hist_df = pd.DataFrame(history.history)
                st.line_chart(hist_df[["loss", "val_loss"]])
                if "accuracy" in hist_df.columns:
                    st.line_chart(hist_df[["accuracy", "val_accuracy"]])

                st.session_state.processing_steps.append(
                    f"Trained CNN model with {epochs} epochs on {len(feature_cols)} features."
                )

            except Exception as e:
                st.error(f"❌ Error during model training: {e}")
                st.session_state.trained_model = None

    # --- Model Inference ---
    st.subheader("🔮 Make Predictions")
    if st.session_state.trained_model:
        st.success("A trained model is available for predictions.")
        if st.button("Predict on Test Data"):
            with st.spinner("Making predictions..."):
                try:
                    predictions = predict_with_cnn(
                        st.session_state.trained_model, X_test
                    )
                    if num_classes > 1 and hasattr(st.session_state, "label_encoder"):
                        predictions_decoded = (
                            st.session_state.label_encoder.inverse_transform(
                                np.argmax(predictions, axis=1)
                            )
                        )
                        y_test_decoded = (
                            st.session_state.label_encoder.inverse_transform(y_test)
                        )
                        st.write("Sample Predictions (decoded):")
                        st.dataframe(
                            pd.DataFrame(
                                {
                                    "Actual": y_test_decoded[:10],
                                    "Predicted": predictions_decoded[:10],
                                }
                            )
                        )
                    else:
                        st.write("Sample Predictions:")
                        st.dataframe(
                            pd.DataFrame(
                                {
                                    "Actual": y_test[:10],
                                    "Predicted": predictions[:10].flatten(),
                                }
                            )
                        )

                    st.session_state.processing_steps.append(
                        "Made predictions using the trained CNN model."
                    )

                except Exception as e:
                    st.error(f"❌ Error during prediction: {e}")
    else:
        st.info("Train a model first to enable predictions.")

    # --- Save/Load Model ---
    st.subheader("💾 Save/Load Model")
    model_name = st.text_input("Model Name (for saving/loading)", "my_cnn_model")
    col_save, col_load = st.columns(2)

    with col_save:
        if st.session_state.trained_model and st.button("Save Model"):
            try:
                save_model(st.session_state.trained_model, model_name)
                st.success(f"✅ Model '{model_name}' saved successfully!")
                st.session_state.processing_steps.append(
                    f"Saved CNN model: {model_name}"
                )
            except Exception as e:
                st.error(f"❌ Error saving model: {e}")

    with col_load:
        if st.button("Load Model"):
            try:
                loaded_model = load_model(model_name)
                st.session_state.trained_model = loaded_model
                st.success(f"✅ Model '{model_name}' loaded successfully!")
                st.session_state.processing_steps.append(
                    f"Loaded CNN model: {model_name}"
                )
            except Exception as e:
                st.error(f"❌ Error loading model: {e}")

    st.markdown("---")

    # Navigation
    if st.button("➡️ Proceed to Real-time Analysis", type="primary"):
        st.query_params["step"] = 9  # Update query param for navigation
        st.rerun()
