# binarymaskTool
Simple tool for binary ground truth mask.
The example image is from PlantVillage( https://www.kaggle.com/datasets/emmarex/plantdisease )
![image](https://github.com/user-attachments/assets/a3ff37de-4cc3-48cc-8e0d-39140b5904e5)
and the result is :
![image](https://github.com/user-attachments/assets/52a48416-c481-43a6-8367-8c5893591f4e)

# Mask Annotator

A single-file lightweight binary mask annotation tool for image segmentation tasks.  
Supports polygon drawing and GrabCut-based region selection.

#Features

- 🖱️ Left click: Add polygon point  
- ⇧ Shift + Left click: Fill polygon  
- ⇧ Shift + Ctrl + Left click: Erase polygon  
- 🖱️ Right click: Cancel polygon  
- 🖱️ Middle click (Wheel) & drag: Select area for GrabCut  
- ⬅️➡️ Arrow keys: Navigate images  (previous/next images)
- ⏎ Enter: Save mask and go to next image  

#How to Use
python3 binarymaskTool.py --category your_category_name



