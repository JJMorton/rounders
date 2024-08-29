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

function fancyNumberInput(id) {
	const dec = document.querySelector(`.fancy-number-dec[for='${id}']`);
	const inc = document.querySelector(`.fancy-number-inc[for='${id}']`);
	const inp = document.getElementById(id);
	dec.addEventListener('click', () => inp.stepDown());
	inc.addEventListener('click', () => inp.stepUp());
}

window.addEventListener("load", function() {

	for (const elt of document.getElementsByClassName('can-toggle')) {
		if (!elt.id) continue;
		const inverse = elt.classList.contains('inverse')
		const toggle = document.querySelector(`input[type="checkbox"][for="${elt.id}"]`)
		if (!toggle) continue;
		const update = () => elt.disabled = inverse ? toggle.checked : !toggle.checked;
		toggle.addEventListener('change', update);
		update();
	}

});
