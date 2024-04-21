Structure of the database containing all the players, teams, and matches.
All fields are NOT NULL.

- `teams` table - The teams formed each year
	- `id` INTEGER PRIMARY KEY
	- `name` TEXT
	- `year` INTEGER

- `players` table - People that have registered at any point
	- `id` INTEGER PRIMARY KEY
	- `name_first` TEXT
	- `name_last` TEXT

- `members` - The players in each team, can have duplicate `player_id`s if a player played in multiple teams or during more than one year
	- `player_id` INTEGER
	- `team_id` INTEGER
	- PRIMARY KEY(`player_id`, `team_id`)

- `matches` - The matches played
	- `id` INTEGER PRIMARY KEY
	- `team1_id` INTEGER
	- `team2_id` INTEGER
	- `score1` REAL
	- `score2` REAL
	- `play_date` INTEGER
