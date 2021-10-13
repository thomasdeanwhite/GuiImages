# GuiImages

A labeled dataset of images showing common GUI components.

![alt text](https://raw.githubusercontent.com/thomasdeanwhite/GuiImages/master/assets/training_data.png "Bounding boxes derived from a Java Swing Ripper")

Currently there are 10 components supported:
- Text Field
- Button
- Combo Box
- Tree
- List
- Scroll Bar
- Menu Item
- Menu
- Toggle Button (checkbox or radio button)
- Tabs

A model has been trained from this dataset to automatically identify GUI componenets in screenshots, here are a sample of identifications taken from the test set:

![alt text](https://raw.githubusercontent.com/thomasdeanwhite/GuiImages/master/assets/pred-128.jpg "Bounding boxes generated on model trained with dataset")
![alt text](https://raw.githubusercontent.com/thomasdeanwhite/GuiImages/master/assets/pred-136.jpg "Bounding boxes generated on model trained with dataset")
![alt text](https://raw.githubusercontent.com/thomasdeanwhite/GuiImages/master/assets/pred-187.jpg "Bounding boxes generated on model trained with dataset")