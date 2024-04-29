window.addEventListener('load', async function() {

	'use strict'

	const addButton = document.getElementById('button-create-team');
	const addDialog = document.getElementById('dialog-create-team');
	addButton.addEventListener("click", () => addDialog.showModal());

	const removeButton = document.getElementById('button-remove-teams');
	const removeDialog = document.getElementById('dialog-remove-teams');
	removeButton.addEventListener("click", () => removeDialog.showModal());

	const playersContainer = document.getElementById("available-players");
	const teamsContainer = document.getElementById("available-teams");

	(await paginated('/api/players'))
		.forEach(player => {
			const li = document.createElement("li");

			const cb = document.createElement("input");
			cb.type = "checkbox";
			cb.name = "players";
			cb.value = player.id;
			cb.id = `player${player.id}`;

			const label = document.createElement("label");
			label.innerText = `${player.name_first} ${player.name_last}`;
			label.setAttribute('for', cb.id);

			li.appendChild(cb);
			li.appendChild(label);
			playersContainer.appendChild(li);
		});

	(await paginated(`/api/teams?year=${window.year}`))
		.forEach(team => {
			const li = document.createElement("li");

			const cb = document.createElement("input");
			cb.type = "checkbox";
			cb.name = "teams";
			cb.value = team.id;
			cb.id = `team${team.id}`;

			const label = document.createElement("label");
			label.innerText = team.name;
			label.setAttribute('for', cb.id);

			li.appendChild(cb);
			li.appendChild(label);
			teamsContainer.appendChild(li);
		})

})