Structure of the database containing all the players, teams, and matches.

- `teams` table - The teams formed each year
	- `id` INTEGER
	- `name` TEXT
	- `year` INTEGER

- `players` table - People that have registered at any point
	- `id` INTEGER
	- `name_first` TEXT
	- `name_last` TEXT

- `members` - The players in each team, can have duplicate `player_id`s if a player played in mmultiple teams or during more than one year
	- `id` INTEGER
	- `player_id` INTEGER
	- `team_id` INTEGER

- `matches` - The matches played
	- `id` INTEGER
	- `team1_id` INTEGER
	- `team2_id` INTEGER
	- `score1` REAL
	- `score2` REAL
