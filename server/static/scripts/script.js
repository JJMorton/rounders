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
