function confirmDialog(title, action, method='POST') {
	if (confirm(title)) {
		const form = document.createElement('form');
		form.method = method;
		form.action = action;
		document.body.appendChild(form);
		form.submit();
	}
}

function parentWithClass(elt, cls) {
	let e = elt;
	while (e !== null && !e.classList.contains(cls)) {
		e = e.parentElement;
	}
	if (!e) throw Error(`Could not find parent with class ${cls} of element`, elt);
	return e;
}

function addRow(button) {
	const outer = parentWithClass(button, 'many-row-input');
	const templ = outer.querySelector('template');
	if (!templ) throw Error('No template found in .many-row-input');

	const newRow = templ.content.cloneNode(true);
	const input = newRow.querySelector('input');
	outer.appendChild(newRow);
	// Focus the first input if there is one
	if (input) input.focus();
}

function removeRow(button) {
	const row = parentWithClass(button, 'row');	
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

