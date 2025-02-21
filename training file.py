import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix
import numpy as np
import seaborn as sns
from sklearn.preprocessing import label_binarize
import ssl

# Bypass SSL certificate verification (specific to macOS issue)
ssl._create_default_https_context = ssl._create_unverified_context

# Set image size and batch size
IMG_HEIGHT = 256
IMG_WIDTH = 256
BATCH_SIZE = 32

train_dir = 'Brain Tumor MRI Dataset/Training'
test_dir = 'Brain Tumor MRI Dataset/Testing'

# Data preprocessing and augmentation
train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

test_datagen = ImageDataGenerator(rescale=1. / 255)

# Loading training and testing data
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

# Load pre-trained DenseNet121 model (Transfer Learning)
base_model_densenet = DenseNet121(weights=None, include_top=False, input_shape=(IMG_HEIGHT, IMG_WIDTH, 3))
base_model_densenet.load_weights('densenet121_weights_tf_dim_ordering_tf_kernels_notop.h5')  # Ensure correct path for weights

# CNN Model Layer
cnn_model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D(2, 2),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(4, activation='softmax')
])

# Combine DenseNet121 and CNN models into one
combined_input = layers.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3))

# DenseNet121 part
densenet_output = base_model_densenet(combined_input)
densenet_output = layers.GlobalAveragePooling2D()(densenet_output)
densenet_output = layers.Dense(512, activation='relu')(densenet_output)

# CNN part
cnn_output = cnn_model(combined_input)

# Concatenate outputs from DenseNet121 and CNN models
merged_output = layers.concatenate([densenet_output, cnn_output])

# Final output layer
final_output = layers.Dense(4, activation='softmax')(merged_output)

# Build and compile the model
model = models.Model(inputs=combined_input, outputs=final_output)

model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Model summary
model.summary()

# Callbacks for training
callbacks = [
    EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    ModelCheckpoint('brain_tumor_cnn_best_model.keras', save_best_only=True),  # Save best model in .keras format
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)
]

# Set steps per epoch and validation steps
steps_per_epoch = 80
validation_steps = 80

# Train the model
history = model.fit(
    train_generator,
    epochs=21,  # Adjust as needed
    steps_per_epoch=steps_per_epoch,
    validation_data=test_generator,
    validation_steps=validation_steps,
    verbose=1,
    callbacks=callbacks
)

# Save the final model in .keras format
model.save('brain_tumor_cnn_final_modelpooi.keras')  # Use the native Keras format

# Save the model weights with the correct suffix
model.save_weights('brain_tumor_cnn_GHJweightspoi.weights.h5')  # Ensure '.weights.h5' is used

# Evaluate the model
test_loss, test_acc = model.evaluate(test_generator)
print(f"Test loss: {test_loss}, Test accuracy: {test_acc}")

# Get true labels and predictions for ROC Curve and Confusion Matrix
true_labels = test_generator.classes
predictions = model.predict(test_generator, verbose=1)

# One-hot encode the true labels for ROC Curve
true_labels_one_hot = label_binarize(true_labels, classes=[0, 1, 2, 3])

# Compute ROC curve and AUC for each class
fpr, tpr, _ = roc_curve(true_labels_one_hot.ravel(), predictions.ravel())
roc_auc = auc(fpr, tpr)

# Plot ROC Curve
plt.figure(figsize=(8, 8))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc='lower right')
plt.savefig('roc_curve1.png')
plt.show()

# Confusion Matrix
cm = confusion_matrix(true_labels, np.argmax(predictions, axis=1))

# Plot Confusion Matrix using Seaborn
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=test_generator.class_indices.keys(), yticklabels=test_generator.class_indices.keys())
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.savefig('confusion_matrix2.png')
plt.show()

# Plot accuracy and loss curves
plt.figure(figsize=(12, 6))

# Plot training & validation accuracy
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Training and Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

# Plot training & validation loss
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

plt.savefig('accuracy_loss_plot3.png')
plt.show()
