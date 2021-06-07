# sprites
Welcome to the Github repository for the SPRITEs (pronounced sprites) NVDA addon. SPRITEs, here by pronounced and refered to as Sprites, stands for Spatial Region Interaction Techniques -- a set of techniques to navigate information spatially using the keyboard. This addon is a research product developed by researchers at the [Make4All](https://make4all.org/) group group at the University of Washington based on [research](https://make4all.org/portfolio/nonvisual-interaction-techniques-at-the-keyboard-surface/) that demonstrates that these techniques could improve efficiency of keyboard navigation. Information on this page will give you a brief overview of the Addon's functionality. Please refer to our [tutorial](https://make4all.github.io/sprites/tutorial/tutorial.html) to get an in-depth understanding of the functionality of this addon. You can [download our addon from the releases page]

## Overview

Sprites is a table navigation mode that can be activated when a user navigates to a table using NVDA's browse mode on Google Chrome by pressing NVDA+shift+t. Once activated, the top row on which the mode is activated is mapped to the top row of keys on the users keyboard (` to =) and the column that is selected using these top row keys is mapped to the left-most column of keys on the user's keyboard (typically `,tab,shift and control). Here are a few important shortcuts.

### Gestures

Activating Sprites mode: <kbd>NVDA</kbd>+<kbd>Shift</kbd>+<kbd>T</kbd>

Note that once Sprites mode is activated, all existing gestures from NVDA will be disabled until the user quits Sprites mode with Escape, and only the keys defined below can be activated:

* Table exploration:
    * For switching columns: keys <kbd>1</kbd> to <kbd>9</kbd> and -, =
    * For switching rows: keys `, tab, capslock, left shift, and left control
    * For announcing row number: r
    * For announcing column number: c
    * For announcing both: b
* search
    * Activating search mode: F
    * Jumping between search results (if any): up arrow and down arrow
    * Exiting search (when in search mode): Escape
* misc
    * Exiting Sprites mode (when not in search mode): Escape
    * Interrupt speech: right shift, right control

Please [visit our tutorial](https://make4all.github.io/sprites/tutorial/tutorial.html) to learn more about how to use sprites, [file a bug](https://github.com/make4all/sprites/issues) if you find an issue, and read our [documentation](https://github.com/make4all/sprites/wiki/internals) if you would like to [contribute](https://github.com/make4all/sprites/wiki/contributing) to Sprites. We look forward to hear more about how you use Sprites!