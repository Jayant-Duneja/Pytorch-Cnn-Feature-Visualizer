import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, random_split, SubsetRandomSampler

import torchboard as tb

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="torch")


class MNISTToRGB(object):
    def __call__(self, img):
        # Replicate the single-channel image into three channels
        img = torch.cat([img, img, img], dim=0)
        return img


# Define the SmallCNN model
class SmallCNN(nn.Module):
    def __init__(self):
        super(SmallCNN, self).__init__()
        self.conv1 = nn.Conv2d(
            3, 16, kernel_size=3, stride=1, padding=1
        )  # Modified for grayscale images
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.fc_dim = 0
        self.set_fc_dim()

        self.fc1 = nn.Linear(self.fc_dim, 64)
        # Adjusted input size based on image dimensions
        self.relu3 = nn.ReLU()
        self.fc2 = nn.Linear(64, 10)

    def set_fc_dim(self):
        x = torch.randn(1, 3, 224, 224)
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)
        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)
        x = x.view(x.size(0), -1)
        self.fc_dim = x.size(1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)
        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.relu3(x)
        x = self.fc2(x)
        return x


# Initialize torchboard
tb.init(username="kaustubh", project_id="mnist-cnn", model_class=SmallCNN)

# Download and preprocess MNIST dataset
transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),
        MNISTToRGB(),
        transforms.Resize((224, 224)),
    ]
)

full_dataset = torchvision.datasets.MNIST(
    root="./data", train=True, download=True, transform=transform
)

# Split the dataset into training, validation, and testing sets
train_size = int(0.8 * len(full_dataset))
val_size = len(full_dataset) - train_size

train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

test_dataset = torchvision.datasets.MNIST(
    root="./data", train=False, download=True, transform=transform
)

# Create dataloaders for each split
batch_size = 4

train_loader = DataLoader(
    train_dataset, batch_size=batch_size, shuffle=True, num_workers=2
)
val_loader = DataLoader(
    val_dataset, batch_size=batch_size, shuffle=False, num_workers=2
)
test_loader = DataLoader(
    test_dataset, batch_size=batch_size, shuffle=False, num_workers=2
)

# Initialize the model, loss function, and optimizer
device = torch.device("cuda")

model = SmallCNN()
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

# Training loop for 6 epochs
for epoch in range(1, 7):
    running_loss = 0.0
    total = 0
    for i, data in enumerate(train_loader, 0):
        inputs, labels = data
        inputs = inputs.to(device)
        labels = labels.to(device)

        total += labels.size(0)

        optimizer.zero_grad()
        outputs = model(inputs)

        loss = criterion(outputs, labels)
        loss.backward()

        optimizer.step()

        running_loss += loss.item()

    tb.log({"epoch": epoch, "train-loss": running_loss / total})

    # Validation
    correct = 0
    total = 0
    with torch.no_grad():
        for data in val_loader:
            images, labels = data
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f"Accuracy on the validation set: {100 * correct / total:.2f}%")
    tb.log({"epoch": epoch, "val-acc": (100 * correct / total)})

    # Testing
    correct = 0
    total = 0
    with torch.no_grad():
        for data in test_loader:
            images, labels = data
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f"Accuracy on the test set: {100 * correct / total:.2f}%")
    tb.log({"epoch": epoch, "test-acc": (100 * correct / total)})

    # Get torchboard data every 3 epochs in zip files
    if epoch % 3 == 0:
        tb.visualize_convs(model)
        tb.download_graphs(f"./downloaded_zips/graphs-{epoch}.zip")
        tb.download_visualizations(
            f"./downloaded_zips/visualizations-{epoch}.zip"
        )

print("Finished Training")

torch.save(model, "mnist_model.pt")
