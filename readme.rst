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
4. (Recommended) Add an object layer and place:

	- ``spawn`` point object for player spawn.
	- ``exit`` rectangle object for level completion zone.
	- Optional ``moving_hazard`` rectangle object for bouncing hazards.

	  - Optional custom properties: ``speed_x`` and ``speed_y`` (numbers).

5. Save the new map as ``assets/levelN.json``.

To add a new level to the game loop:

1. Open ``pysnoopy/levels.py``.
2. Add a new ``LevelSpec`` entry in ``get_default_levels()`` with your map path.
3. (Optional) Add a custom hook class only if the level needs special Python behavior.

Level maps are validated at load time. Required tile layers are ``ground``, ``obstacles``, and ``foreground``.
If ``spawn``/``exit`` objects are missing, the game falls back to legacy spawn and right-edge transition behavior.
``moving_hazard`` objects are loaded directly from Tiled, so hazard-heavy levels can be authored without Python changes.

Quick Test Checklist
--------------------

After editing or adding levels:

0. Validate all configured levels:

	.. code-block:: bash

	python -m pysnoopy.validate_levels

	Use strict mode in CI or pre-commit checks:

	.. code-block:: bash

	python -m pysnoopy.validate_levels --strict

1. Run the game:

	.. code-block:: bash

	python -m pysnoopy.main

2. Move through the level and verify:

	- Ground collisions behave correctly on the ``ground`` layer.
	- Death collisions trigger only on intended ``obstacles`` tiles.
	- Decorative tiles on ``foreground`` render in front of the player where expected.
3. Reach the level end and confirm level transitions still work.
