import os
import cv2
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import ConvLSTM2D, BatchNormalization, Flatten, Dense
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from google.colab import drive


drive.mount('/content/drive')


dataset_path = "/content/drive/MyDrive/dataset"
train_real = os.path.join(dataset_path, "train/real_video")
train_fake = os.path.join(dataset_path, "train/attack")
test_real = os.path.join(dataset_path, "test/real_video")
test_fake = os.path.join(dataset_path, "test/attack")


img_size = 64
num_frames = 20

def extract_frames(video_path, max_frames=num_frames):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while len(frames) < max_frames and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (img_size, img_size))
        frames.append(frame)
    cap.release()
    if len(frames) == 0:
        return None
    while len(frames) < max_frames:
        frames.append(frames[-1])
    return np.array(frames)

def load_dataset(path_real, path_fake):
    X, y = [], []
    for folder, label in [(path_real, "real"), (path_fake, "fake")]:
        if not os.path.exists(folder):
            print(f"⚠️ Warning: {folder} not found.")
            continue
        for file in os.listdir(folder):
            if file.lower().endswith((".mp4", ".avi")):
                video_path = os.path.join(folder, file)
                frames = extract_frames(video_path)
                if frames is not None and frames.shape[0] == num_frames:
                    X.append(frames)
                    y.append(label)
    return np.array(X), np.array(y)

print("🔄 Loading training videos...")
X_train, y_train = load_dataset(train_real, train_fake)

print("🔄 Loading testing videos...")
X_test, y_test = load_dataset(test_real, test_fake)

print("✅ X_train shape:", X_train.shape)
print("✅ X_test shape:", X_test.shape)


if X_train.shape[0] == 0 or X_test.shape[0] == 0:
    raise Exception("❌ No video data loaded. Please check that the folders contain .mp4 or .avi videos.")


X_train = X_train / 255.0
X_test = X_test / 255.0


X_train = X_train.reshape(-1, num_frames, img_size, img_size, 3)
X_test = X_test.reshape(-1, num_frames, img_size, img_size, 3)


le = LabelEncoder()
y_train_encoded = to_categorical(le.fit_transform(y_train))
y_test_encoded = to_categorical(le.transform(y_test))


model = Sequential([
    ConvLSTM2D(32, (3, 3), activation='relu', return_sequences=False, input_shape=(num_frames, img_size, img_size, 3)),
    BatchNormalization(),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(2, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])


model.fit(X_train, y_train_encoded, validation_data=(X_test, y_test_encoded), epochs=10, batch_size=2)


model_save_path = os.path.join(dataset_path, "conv_lstm_model.h5")
model.save(model_save_path)
print(f"✅ Model saved at: {model_save_path}")