function confirmDialog(title, action, method='POST') {
	if (confirm(title)) {
		const form = document.createElement('form');
		form.method = method;
		form.action = action;
		document.body.appendChild(form);
		form.submit();
	}
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

window.addEventListener('load', function() {

	for (const elt of document.getElementsByClassName('fancy-number-inc')) {
		const inp = document.getElementById(elt.getAttribute('for'));
		elt.addEventListener('click', () => inp.stepUp());
	}

	for (const elt of document.getElementsByClassName('fancy-number-dec')) {
		const inp = document.getElementById(elt.getAttribute('for'));
		elt.addEventListener('click', () => inp.stepDown());
	}

	for (const label of document.getElementsByClassName('label-team1')) {
		const select = document.getElementById('select-team1');
		const update = () => {
			label.textContent = select.options[select.selectedIndex].text;
		}
		select.addEventListener('input', update);
		update();
	}

	for (const label of document.getElementsByClassName('label-team2')) {
		const select = document.getElementById('select-team2');
		const update = () => label.textContent = select.options[select.selectedIndex].text;
		select.addEventListener('input', update);
		update();
	}

});

