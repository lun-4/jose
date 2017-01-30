messages:
	xgettext -a --files-from=POTFILES.in --from-code=UTF-8 --directory=.. --output=messages.po

pofiles:
	msginit --locale=en --input=messages.po
	msginit --locale=pt --input=messages.po

clear:
	rm *.po
