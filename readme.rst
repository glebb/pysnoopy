pySNOOPY
=====================

Remake of classic C64 game Snoopy using Python + arcade.

Setup
-----

Create and activate a virtual environment, then install dependencies:

.. code-block:: bash

	python -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt

Run
---

Start the game with the package entrypoint:

.. code-block:: bash

	python -m pysnoopy.main

Start directly from a specific level (1-based):

.. code-block:: bash

	python -m pysnoopy.main --start-level 3

Level Editing and Creation
--------------------------

Levels are Tiled maps stored as JSON files under ``assets/``.

Recommended workflow:

1. Open ``snoopy_tiles.tiled-project`` in Tiled Map Editor.
2. Edit an existing map (for example ``assets/level1.json``) or copy ``assets/template.json`` to a new file.
3. Keep these layer names exactly: ``ground``, ``obstacles``, ``foreground``.
4. Save the new map as ``assets/levelN.json``.

To add a new level to the game loop:

1. Add a new level class in ``pysnoopy/levels.py`` that points ``self.map`` to your new JSON file.
2. Import that class in ``pysnoopy/views.py``.
3. Add it to ``self.levels`` in ``GameView``.

Quick Test Checklist
--------------------

After editing or adding levels:

1. Run the game:

	.. code-block:: bash

	python -m pysnoopy.main

2. Move through the level and verify:

	- Ground collisions behave correctly on the ``ground`` layer.
	- Death collisions trigger only on intended ``obstacles`` tiles.
	- Decorative tiles on ``foreground`` render in front of the player where expected.
3. Reach the level end and confirm level transitions still work.
