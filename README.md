# steam-dmenu

Reads installed Steam apps/games from all libraries referenced in the given `libaryfolder.vdf` file. Can be used to either launch dmenu with the apps/games as selectable options, or generates shell scripts in a folder, to be used as dmenu program location, to be listed in users default dmenu.

## Requirements
- Steam
- python 3.9+
- python-vdf for reading Valve's VDF format
- xdg-open
- dmenu or dmenu compatible application (dmenu, rofi, bemenu, wofi...)

## Significant differences in the fork
The library parameter only allows for one library folder to be given, reason being, if a library isn't defined in the active installations `libraryfolders.vdf`, there will be issues to launch an app or game anways.
You can hide certain apps/games, since you probably don't want tools like Proton to show up, or if you know you know.
Enforcing python 3.9+, because I prefer the type hinting being even further integrated, as it makes it easier to understand what a variable or functions is supposed to do or store.
Using python-vdf again, as it allows to easier read the files, but I am open to write my own parser for that.
Customizing the display of the apps/games in dmenu.
You can generate scripts to integrate the launching of games more tightly, so that you don't need to execute this program and then select your game.

## Configuration
### dmenu compatible application
While dmenu is the default, any compatible alternative or additional parameters for dmenu can be used with the `--dmenu` (`-d`) flag.
#### Default
`dmenu -i`
This means, it will use dmenu and be case-insensetive.
#### Example for rofi:
`steam_dmenu.py -d "rofi -dmenu -i"`

### libraryfolders.vdf
This is the location of the `libraryfolders.vdf` file. It is assumed to be in `~/.local/share/Steam/steamapps/libraryfolders.vdf`, however the `--library` (`-l`) flag can take an alternative path.
#### Default
`~/.local/share/Steam/steamapps/libraryfolders.vdf`
This is default steam library folder on many distros. Usually it is outside of `steamapps`, if the library folder is not the main library. It will try to locate it in a folder or it's existing `steamapps` sub folder, if the file itself is not given.
#### Example
`steam_dmenu.py -l "/home/user/other/steam/library/folder/libraryfolders.vdf"`

### Which prefix to show in dmenu
If you want your apps/games to appear in dmenu with a prefix like `play`, you can use the parameter `--prefix` (`-p`).
#### Default
`play `
The space is inserted, because internally it isn't further formatted and is used as is, to make the code more readable and less complex. So if you want a space inbetween the prefix and your app/game title, you have to add a space.
#### Example "Meow " resulting in "Meow [Name of the App/Game]"
`steam_dmenu.py -p "Meow "`

### Hiding certain games from dmenu
You can also hide certain apps/games, by giving a list of appids for the `--blocked` (`-b`) parameter. By default Proton and some other steam tools are hidden.
#### Default
If parameter isn't used, the output of the `default_blocked_appids` function in `steam_dmenu.py` is used. Give empty string to use no block list.
#### Example for blocking just Team Fortress 2 and Half-Life 2
`steam_dmenu.py -b "440,220"`

### Generate scripts
If you want to generate scripts to be used in dmenu for launching, use `--output` (`-o`). The folder needs to exist, otherwise the application will close without generating the scripts. It overwrites existing scripts that use the same prefix. It only relies on the appid, not the path of the stored application.
#### Default
By default doesn't generate and launches dmenu.
#### Example with xmonad
`steam_dmenu.py -o "~/.xmonad/dmenu/steam"`

### Mode
You can launch the custom dmenu and also generate scripts both at once. Use the parameter `--mode` (`-m`) with the corresponding mode number.
#### Options
`0`: Just launch
`1`: Generate scripts
`2`: Generate scripts, then launch
#### Default
`0`
#### Example generating and launching
`steam_dmenu.py -m 2`
