# Shattered Marches

## Run the PyQt6 game

Install the GUI dependency if it is not already available:

```powershell
python -m pip install -r requirements.txt
```

Start the desktop game:

```powershell
python main.py
```

The original terminal interface remains available:

```powershell
python main.py --cli
```

The PyQt6 interface draws its pixel-art characters, terrain, and battle impact
effects procedurally with Qt, so no external sprite pack is required.

## Story authoring

Create an editable story template:

```powershell
python story_tool.py init my_story.json
```

Validate it, then export its quests and world events:

```powershell
python story_tool.py validate my_story.json
python story_tool.py export my_story.json
```

## Custom equipment crafting

The guild's Blacksmith lets a character forge a named weapon or armor item using
its level and a material. Higher character levels unlock stronger tiers.

- Weapon types: Sword, Axe, Spear, Bow, Staff, Dagger
- Armor types: Light Armor, Chain Armor, Plate Armor, Robes
- Materials: Iron, Steel, Mithril, Dragon Scale, Frost Crystal, Storm Metal

## Expanded crafting materials

Materials can be:

- Purchased in town shops
- Mined or gathered in wild map locations
- Dropped by enemies
- Refined into components using crafting recipes

The same material behaves differently depending on its placement:

- Weapons: blade, core, or binding
- Armor: plate, lining, or enchantment
- Accessories and helms use the compatible role bonuses

## Strongholds

The party begins with a customizable stronghold. Available types are Hideout,
Fortress, Temple, Academy, and Estate.

The stronghold catalog contains 200 improvements across Defense, Economy,
Crafting, Training, Magic, Exploration, and Sanctuary categories. Improvements
have gold costs, level prerequisites, type compatibility, and passive bonuses.

## Skill progression

Characters receive skill points whenever they level:

- No magic: 6 skill points
- Low magic: 4 skill points
- Medium magic: 3 skill points
- Full magic: 2 skill points

Skills have level gates, point costs, prerequisites, power scaling, categories,
and optional elemental, status, and target effects. Custom skill trees can be
registered with `create_skill_tree(root_name, root_skill, branches)`.

## Android / PWA

Start the touch-friendly mobile server:

```powershell
python main.py --android
```

Open `http://localhost:8080` on the phone or tablet browser. To use it on
another Android device, start the server on a computer and open
`http://COMPUTER-LAN-IP:8080` in Chrome. The phone and computer must be on the
same network.

Use Chrome's **Install app** or menu **Add to Home screen** option to install
the PWA. To select another port:

```powershell
python main.py --android 9090
```

## Android APK packaging

The native Android project is in [android/](/C:/Users/ddandurand01/python%20exercises/practices_and_tests/rpg%202%20test/android).
It uses Chaquopy to run the Python game inside an Android WebView.

To build locally, install Android Studio, JDK 17, Android SDK 35, and Gradle,
open `android/`, then run:

```powershell
.\gradlew assembleDebug
```

The debug APK is written to:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

On GitHub, push the project or run the **Build Android APK** workflow. It uploads
`Shattered-Marches-debug.apk` as a workflow artifact.

## Controls

- Move on the map with **W/A/S/D** or the **arrow keys**.
- Click an orthogonally adjacent map tile to move one step.
- Walk onto a location tile to interact with the inn, shop, guild, quest board,
  arena, or special event.
- Combat actions are selected with buttons. Skills, targets, and items are
  chosen from dialogs.
- Use **Save** in the game window. Save data is stored beside `main.py`.

## Tests

Run the project tests with:

```powershell
python -m unittest discover -s tests -v
```
