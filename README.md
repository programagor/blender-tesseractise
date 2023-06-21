# blender-tesseractise
Blender plugin that projects the selected objects onto cells of a 4D tesseract, and then projects the result back into 3D space

## Installation
1. Download the `tesseractise.py` file
2. Open Blender > Edit > Preferences > Add-ons
3. Click Install
4. Select the `tesseractise.py` file
5. Enable the plugin

![image](https://github.com/programagor/blender-tesseractise/assets/7930007/7d2be9aa-66f9-4e20-8e11-edd278849495)


## Usage
1. Select the objects that you wish to tesseractise

![image](https://github.com/programagor/blender-tesseractise/assets/7930007/ddfd3f51-1141-46b6-bbce-3cb920580978)

2. Click Object > Tesseractise (of F3 and search "Tesseractise")

![image](https://github.com/programagor/blender-tesseractise/assets/7930007/cbff6caf-ac2e-4d3b-8736-8e3e25b55090)

3. Adjust the parameters

![image](https://github.com/programagor/blender-tesseractise/assets/7930007/a9b4fa98-0754-4ccb-8095-17e4235ce56e)

4. Confirm

![image](https://github.com/programagor/blender-tesseractise/assets/7930007/ab25d138-bb09-4695-b70a-f133ffd6f90c)

## Parameters
- W scale: Scaling factor for all positions along the W axis
- Camera distance: Distance between the 4D camera and the origin
- Projection: Which method is used for converting from 4D to 3D
  - Perspective: Simple perspective projection (maintains straight lines)
  - Fish-eye: Mirror ball fish-eye projection (introduces distortion)
  - Orthographic: Orthographic projection (infinite viewing distance, not useful)
- Tesseract cells to generate: Selects which cells of the tesseract should the source object be projected to (The W+ cell is the outed 4D cell which usually ends up inside out and on top of everything else)
- 4D rotations: Specifies the rotation plane and angle to apply before converting from 4D to 3D. If multiple rotations are specified, they are applied in the order they are listed in.
