async function paginated(url) {

	url = window.location.origin + url;

	results = [];

	for (let page = 1;; page++) {

		url = new URL(url);
		url.searchParams.set("page", page);
		const res = await fetch(url);
		if (!res.ok) break;

		res.json()
			.then(json => {
				json['data'].forEach(x => results.push(x));
			})
			.catch(console.error);
	}

	return results;
}

function confirmDialog(title, action) {
	document.getElementById("confirm-title").textContent = title;
	document.getElementById("confirm-form").setAttribute("action", action);
	document.getElementById("dialog-confirm-action").showModal();
}

function parentOfType(elt, tag) {
	let e = elt;
	while (e !== null && e.tagName.toLowerCase() !== tag.toLowerCase()) {
		e = e.parentElement;
	}
	if (!e) throw Error(`Could not find parent with type ${tag} of element`, elt);
	return e;
}

function addRow(button) {
	const table = parentOfType(button, 'table');
	const templ = table.querySelector('template');
	if (!templ) throw Error('No row template found in table');

	const newRow = templ.content.cloneNode(true);
	const input = newRow.querySelector('input');
	table.querySelector('tbody').appendChild(newRow);
	// Focus the first input if there is one
	if (input) input.focus();
}

function removeRow(button) {
	const row = parentOfType(button, 'tr');	
	row.remove();
}

