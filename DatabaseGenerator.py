# This file is responsible for creating the necessary files for YOLOv4 training
import os
import random
import shutil


class DatabaseGenerator:
    def __init__(self):
        self.rootDirectory = os.getcwd()
        self.yoloDirectory = os.path.join(self.rootDirectory, 'YOLOv4')
        self.databaseDirectory = os.path.join(self.yoloDirectory, 'Complete_Database')
        self.readyDBDirectory = os.path.join(self.databaseDirectory, 'Ready_Database')

        self.objectsDirectories = []
        object1 = str(input('Folder name for the first object: '))
        self.object1Directory = os.path.join(self.databaseDirectory, object1)
        self.objectsDirectories.append(self.object1Directory)

        object2 = str(input('Folder name for the second object: '))
        self.object2Directory = os.path.join(self.databaseDirectory, object2)
        self.objectsDirectories.append(self.object2Directory)

        object3 = str(input('Folder name for the third object: '))
        self.object3Directory = os.path.join(self.databaseDirectory, object3)
        self.objectsDirectories.append(self.object3Directory)

        object4 = str(input('Folder name for the forth object: '))
        self.object4Directory = os.path.join(self.databaseDirectory, object4)
        self.objectsDirectories.append(self.object4Directory)

        object5 = str(input('Folder name for the fifth object: '))
        self.object5Directory = os.path.join(self.databaseDirectory, object5)
        self.objectsDirectories.append(self.object5Directory)

        self.train_file = []
        self.test_file = []

        self.create_db_folder()
        self.create_and_move_db_files()

    # creates the folder where the database will be placed
    def create_db_folder(self):
        if not os.path.exists(self.readyDBDirectory):
            os.chdir(self.databaseDirectory)
            os.mkdir('Ready_Database')
            os.chdir(self.rootDirectory)
        if not os.path.exists(os.path.join(self.readyDBDirectory, 'images')):
            os.chdir(self.readyDBDirectory)
            os.mkdir('images')
            os.chdir(self.rootDirectory)

    # creates the files for the training, separating 80% os the images for train and 20% for test, randomly.
    # moves the images and labels to the right folder for training
    def create_and_move_db_files(self):
        for objectDirectory in self.objectsDirectories:
            images = [f for f in os.listdir(os.path.join(objectDirectory, 'images'))
                      if (os.path.isfile(os.path.join(objectDirectory, 'images', f)) and
                          (f.lower().endswith(('.png', '.jpg', '.jpeg'))))]
            labels = [f for f in os.listdir(os.path.join(objectDirectory, 'labels'))
                      if (os.path.isfile(os.path.join(objectDirectory, 'labels', f)) and
                          (f.lower().endswith('.txt')))]
            for image in images:
                shutil.move(os.path.join(objectDirectory, 'images', image),
                            os.path.join(self.readyDBDirectory, 'images', image))
            for label in labels:
                shutil.move(os.path.join(objectDirectory, 'labels', label),
                            os.path.join(self.readyDBDirectory, 'images', label))
            random.shuffle(images)

            train_images = images[:(len(images) // 10) * 8]
            test_images = images[(len(images) // 10) * 8:]

            for train in train_images:
                self.train_file.append(os.path.join(self.readyDBDirectory, 'images', train))

            for test in test_images:
                self.test_file.append(os.path.join(self.readyDBDirectory, 'images', test))

        os.chdir(self.readyDBDirectory)
        with open('train.txt', 'w') as f:
            for imageAddress in self.train_file:
                f.write("%s\n" % imageAddress)

        with open('test.txt', 'w') as f:
            for imageAddress in self.test_file:
                f.write("%s\n" % imageAddress)

        os.chdir(self.rootDirectory)


if __name__ == '__main__':
    dbg = DatabaseGenerator()

