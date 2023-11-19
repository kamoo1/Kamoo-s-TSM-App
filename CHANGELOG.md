# CHANGELOG



## v0.3.0 (2023-11-19)

### Documentation

* docs: update `README.md` ([`53a3233`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/53a323315e8eb6ad09a6b175b194386079d9d319))

### Feature

* feat(ui): notify user after export / update ([`a66117e`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/a66117e874132d0b8e33f1431f499c8a1743caa9))

* feat(ui): add last update time ([`9f48244`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9f482447aeed7a10e110ab389b9adb56b6aeb5cd))

### Fix

* fix: export data being `None` ([`7256453`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/7256453a9f30a8f35e529f75e8578d677518902a))

* fix: set `ts_compressed` to 0 for combined data ([`720d6ac`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/720d6ac6f9df1dbebe29ab69a588cdd5f83102d8))

* fix: avoid `ts_compressed` mismatch

avoid `ts_compressed` mismatch between meta and records by
introducing locality. ([`8f91717`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/8f91717b13e7d00db1f3ed75364d5aca249d42c8))

* fix: `average_by_day` with `ts_compressed`

cannot just assume db is always being compressed up to yesterday ([`a25b4c8`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/a25b4c8d6bbd7d983565121da8d124f10b996101))

### Performance

* perf: avoid re-compress records ([`0f83fc2`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/0f83fc239ffea1ed025142e2c3a255d2bf1bac7f))


## v0.2.0 (2023-11-04)

### Feature

* feat: cache clean-up on start ([`8533586`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/8533586b0f217a4d21ceede5ed0c94f2c0f363ba))

* feat: github api pagination ([`ab8cc80`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/ab8cc80ccf1c33dbc84b93944ad22d553ba4f87c))

### Fix

* fix: thread update check so it won&#39;t block UI load ([`6378c1c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/6378c1cc088d1f166a4f522d15767bfa4665b8c3))

* fix: save single click checked items in settings ([`724cab5`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/724cab5b08d620e598a3eb3a0beb1af7f2be3fa6))


## v0.1.1 (2023-10-18)

### Fix

* fix: `Pyinstaller` build has `None` for stderr ([`f773e16`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/f773e162eecf7b159fc90c3e8b13f0cd3d0d6d9a))

### Unknown

* doc: update badge ([`2b43598`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2b43598d7dfc1b6d42224db2a950e638cdf9e06a))


## v0.1.0 (2023-10-18)

### Breaking

* feat: hc support and big refactor

BREAKING CHANGE: meta schema changed ([`57df47b`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/57df47bb9c020fe76e3076d497c17b390e708580))

* feat: batch patch

BREAKING CHANGE: removed `patch_tsm`, `--src_digest` now is a file. ([`6ab6206`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/6ab620670e6ab4482e62ef4867289f84741c9c8a))

* fix: remove the hacky export realm fix

BREAKING CHANGE: some new realms need `LibRealmInfo` patched to work. ([`9298fa2`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9298fa262fd74bf003f69a8949d2afd5b78e8770))

### Feature

* feat: client auto update

also migrates to `pydantic` 2.x ([`86da0a8`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/86da0a872ced0e5ad63592fe4042193c40b5615e))

* feat: add backward compatibility for `Meta` files ([`54c0efe`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/54c0efef592294ad4b5054c47ea618b51ffa4bc5))

* feat: add system info collector for `Meta` ([`9a802f1`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9a802f105b68a6aca73944367a20a1658a3648f0))

* feat: add entrypoint for binary release ([`e9113c3`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e9113c33ba7db4b150445d0cdeb3641dd5113362))

* feat: UI

- finishing up internationalization, patching
- fixed few bugs
- refactored entry point for binary release ([`96b4d90`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/96b4d904371bd4f7fdd0afdaa1a36a41efafed57))

* feat: UI

WIP:
add LibRealmInfo patching
localization support ([`8dcec5e`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/8dcec5ec5112c2eb7b3aca459a5d1ae7571af55a))

* feat: add text file patcher ([`4be74eb`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4be74ebe63ca12fae20cbdae15c30c4258660eaf))

### Fix

* fix: few bugs

fix meta bug where unable to label HC for non en_US requests
fix UI bug where widgets gets incorrectly enabled / disabled
fix UI update always take remote mode
improve logging / supress ssl warning ([`a246a3e`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/a246a3e5e076588a9861ef683a8c32a347180407))

* fix: regional price sources were unsorted ([`2f1799c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2f1799c9ecc7df3fbe58a8a9c9d660af90fb9f28))

* fix: random SSL cert error, improve error handling

- ignoring ssl verification due to random SSL cert expire error.
- auctions schema now accepts optional `auctions` field.
- more explicit request error handling ([`4e676cb`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4e676cb210a33552aadce1f181b4955e3e11f087))

* fix: mock warcraft path during testing ([`b44fa0d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/b44fa0d44bf46f9793b3994c7f1154ebda06e3db))

* fix: running without data

many routines of this project doesn&#39;t depend on `bonuses_courves.json`,
make it so it&#39;s able to run them without it. ([`4093659`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4093659980855648b3cd7fed52a867571cfea7da))

* fix: ui freezes while having connection issues

tone down the `backoff_factor` in `GHAPI` ([`59083fd`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/59083fdcdbd5cb79855044412741ac570bfddcb0))

### Unknown

* doc: update readme ([`3082fbd`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/3082fbdafd4859a35aaed0bd0e4441a13bf9e957))

* WIP: UI ([`4288789`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4288789e472ec407943f58eb260cfa13da1d8acb))

* Safety Measure for Python 3.10 `StrEnum` ([`bd56577`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/bd56577ca41bd1a9896f4ce5860d07a960fb9da5))

* Remove Useless Comment ([`3720f2d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/3720f2d702feb32d4fac384e0c0283f5e52712ef))

* WIP: UI ([`c42f309`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/c42f309bd060df24d858ce979e8b94393304ba73))

* Update Tests ([`4773cf0`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4773cf0501c424f1d2120a66cfd218b442bdc0af))

* Add Traceback for `DownloadError` Warning ([`fa1a1c0`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/fa1a1c0416cf3286770a8da6f67de57d9b06d356))

* Improve:
 - Clarify logic of some optional parameters
 - Add `--repo` and `--gh_proxy` options, allowing &#34;remote + local&#34; mode
 - Decrease logging level of failed auction requests to &#34;warning&#34;. ([`5a41e88`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/5a41e880c3c49baedbf36698a75be57a5020f7c8))

* Improve:
 - Clarify logic of some optional parameters
 - Apply recently added validators to argument parser ([`a9bd13b`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/a9bd13bfc55976bf276ef91daa0d095a9248a8cd))

* Improvements:
 - Use custom `DownloadError` to indicate expected downloading errors.
 - Display them as warnings instead of errors.
 - DB mode variable naming change ([`9e11a26`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9e11a262c25b45e951ec30d46fb077c17da31494))

* Validate GH Proxy Scheme ([`0277561`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/0277561752b2ff2d327c92845e2480f7d9fe5798))

* Improve Logging ([`9e69842`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9e6984240afcfe07100ee0683a1e15bea6f125a3))

* Update Requirements ([`0f3cc5f`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/0f3cc5f92b5b07d06cc7665bc4716306f836c7fe))

* WIP: UI Feature ([`119c375`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/119c375693a2e478049281e13363fce6abe9eb66))

* Changes:
 - Add Warcraft bases path validation
 - Some minor changes ([`3d76027`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/3d7602788c2b75eadc1590e7947b5cf8451ac9a6))

* Overload `load_meta`, allow `Namespace`. ([`619d6b5`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/619d6b506f47627fdebdc9c8ac9beb0c49bb3d18))

* Changes:
 - fix URL tailing slash issue
 - add URL validation ([`e3b9740`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e3b974002c93a771caed1dec3603ef0fdcce31f2))

* Support Python3.11 Breaking Change
Fixes #37 ([`e20b58d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e20b58dc15a2822d667f64e235813dd88b0bf49d))

* Standardize Import Statement ([`8362203`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/836220311a9254a2deb4a6ea7f7431639390ff63))

* Tune Down GHAPI Cache TTL ([`f6e85bc`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/f6e85bc316be7f5f1c9c7e318aba5049c4bad4d0))

* Remove Parallelism
There&#39;s a issue that happens by chance when multiple access tokens are used in parallel (i think?). ([`2638bb5`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2638bb5439670d93d1adc262a7659f87992a26ff))

* Update Housekeeping Script
Remove bad classic data ([`e62e16f`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e62e16f34e038a74915e384138fffe33ba6de32e))

* Correct Classic Prices ([`0177963`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/0177963e80e885684e96e5020e6ad25637d09681))

* Correct Classic Prices ([`a75de9d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/a75de9dc12d1a4ea6f640fdb9f33eb2d9bb7b9b4))

* oppsie ([`cfaea0f`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/cfaea0f18b9a9ccdf3f47b937b34110e59c67a56))

* Update Readme ([`4fe1491`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4fe14915e46fedb725b38bcdff7df01e51d6f525))

* Add Korean Region to Update Schedule ([`59bc52c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/59bc52c27c7353e62b3ce12e276104a3a9330530))

* Parallelize Github Workflow
I&#39;ll blame it on Bing if it explodes ([`30f622c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/30f622c5aac3d8b3a900ca0fb8a694540758324e))

* Update Housekeeping Script
I changed the naming yet again :) ([`f0b7e0c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/f0b7e0ce22a856ea837a50e1f2a368e3b995bbf7))

* Support Arbitrary Number of Assets ([`df181ad`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/df181ad12cee3847ae183c05e60af909242e6f82))

* Fix Retail Export ([`cd641ae`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/cd641ae0fcd1206746b2acbcb02c5c856f257e9c))

* Update Readme ([`f43a8be`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/f43a8be4bf1d4fc91c622daa0c8691023b5ad901))

* Update Comment ([`97ff125`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/97ff1254aba46d3f529ca842caa4cc600961ac3d))

* Add Classic Support ([`3708169`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/3708169a5b12b8db9deef6cd08924ab07c41f08f))

* Migrate Internal Models to Attrs ([`4bc03f6`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4bc03f6c645e6ffb1f65512e085cdaf6e26da52e))

* Update Readme ([`674a88e`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/674a88e71cdaee9f987de8553a0aec88eac488a0))

* Add Records Compression:
Compress records since yesterday, into aggregated daily results ([`257f530`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/257f5302145d6effe87f0adf26af16ef26f5044c))

* Correct Exception Message ([`4f295e2`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4f295e22723f534dba41810b45afff015e87b9dd))

* Add Retry and GHProxy to GHAPI ([`bd8bc45`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/bd8bc458c0f80dec668113ff18aaaed4ed5f1d2f))

* Format Error Messages ([`ece70e7`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/ece70e74d544201b919c7007614b752fcd6274bb))

* Update Housekeeping Script ([`e0062a5`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e0062a5fa35c0d90dd8f2e3d1e72568f3542fb96))

* Revert &#34;Keep Empty Game Version in File Name&#34;

This reverts commit 317d08c5cb48ff952af87597cd9ae6f9d6ed322c. ([`6b6329a`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/6b6329a0869fd675f1ca3890b98f2694fce2008b))

* Releasing All JSON Files Under Output ([`6c70d50`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/6c70d506ec43dee4d48a5e17bd83a2f47395b7e7))

* Add Housekeeping Script ([`842a92e`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/842a92ef1cc0f386d300fe9f3bf79f506ccf9a75))

* Add Housekeeping Script ([`d2599f2`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/d2599f2895fc6707e0becfa6fe0da7383c3eff20))

* Add Housekeeping Script and Job ([`ff036e6`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/ff036e6984ac972262db7cac7a473ebf47d47bb1))

* Add Housekeeping Script and Job ([`f62409c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/f62409c2f2e1ae7315f0544600889b1be09d54f5))

* Keep Empty Game Version in File Name ([`317d08c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/317d08c5cb48ff952af87597cd9ae6f9d6ed322c))

* Update Readme
Add roadmap ([`c01cb66`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/c01cb6650900f610f3033d7fd560cb3efead6f3c))

* Game Version Basic Support ([`2e16774`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2e1677409e7aab3d4c6a24deb8d1ef1c61cc400d))

* Rename TaskManager to Updater ([`204a67a`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/204a67a53477557f71ad6bdaf8b16d4fb90c00d3))

* Add AH Update Badge ([`062aed3`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/062aed392dd4e1b961b99308921b94ef3a43841b))

* Remove Deprecated Option ([`68239fd`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/68239fdd883b3d18c18a8a45ca392b01332b1cff))

* Fix Export Data:
&#39;AUCTIONDB_REALM_HISTORICAL&#39; and &#39;AUCTIONDB_REALM_SCAN_STAT&#39; should also contain commodities data ([`9c42698`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9c42698add27c8c4e2cf9e2b58113a4b55573cf5))

* Make Exceptions Meaningful ([`ed994a0`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/ed994a077e9c36f37508689aeb3693fbd7638109))

* Correct Arguments for Exporter:
At least one realm should be given ([`bc2e5fd`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/bc2e5fd8005d461ea523ff5ade00ce4a84a20d99))

* Simplify Command Line Args:
 - Adding default value for DB path
 - Update related command in README ([`c743d31`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/c743d31e3caf6ac9a00216715ba29b1b1d05197f))

* Update `requirements.txt` ([`d79c214`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/d79c21436b338b00232fc8706a42d561a0b44998))

* Update README ([`c73bd9a`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/c73bd9a8519cc267bfd96b128f36b735b2e834c6))

* Changes:
 - rename `task_manager.py` to `updater.py`
 - move updater&#39;s entry to `ah.updater` ([`9a81908`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9a81908ff109cc65e76fee4f23d7567fe48f6a3c))

* Meta Data:
 - add connected realms info so we don&#39;t have to use battle net api when exporting;
 - gathering some basic system info;

Exporter:
 - add argparse ([`a79450d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/a79450df80e7b1b3e07278dda561f91410d94f6d))

* add support for ilvl items in ItemString ([`520eb0d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/520eb0de1bac95d556df052dfcffcb8827248355))

* forgot to save few properties in protobuf of map records ([`bdbb61f`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/bdbb61fe64aee41b10ea6f77712e3c3ab181d5fc))

* wip: some updates ([`4aa989a`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/4aa989afa052c16a4fecbd96064a7bd853190c38))

* add more unittest, some improve on code ([`09a9659`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/09a96592b9fe2113bd05fc40a175b268b64879b9))

* allowing db using remote file`nfinishing up export`nWIP: test ([`68eaaa4`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/68eaaa48e5cf3e9dfee5c8bb1b31a4177584414b))

* also release meta file ([`e3e65f2`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e3e65f250cdf09efe31068103842cca51bd11c85))

* refactoring code, export is in WIP ([`9c3c42d`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9c3c42d85375dd259fb6e3c0673ef4c12c14ac16))

* update job display name ([`c7d00df`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/c7d00df0eb17d07b2c395416ea374f29364ad89f))

* release db files instead ([`5d78144`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/5d781447eabab63a57ccb5a16a9318b006db52f4))

* Changes:`n - pet id should be pet_species_id`n - remove unnessary parameter in from_response ([`85190f0`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/85190f0290563152415e975b8dabb281c33b2f56))

* add warps ([`2b80db3`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2b80db3544f2a31e6834aff0a901ece6eb8ad18c))

* use default locale for realm name that is supported by TSM ([`e7260b0`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e7260b03f5c44a3d71780696bd30e60f40a3e69b))

* update tests ([`b67a494`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/b67a49496d433ded4cdb0011850285c20db6da5c))

* add badge ([`3a9671b`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/3a9671be29246e08eb014e1935a0704c198de481))

* tidy up ([`9074fc4`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9074fc4ab4db0f8dd6f1d7822a55b7b66ef121ac))

* update readme ([`dc36274`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/dc362740044f2e15104c78ba5a33d7b3143f4b04))

* add readme ([`0322d56`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/0322d56d5d5299ebe211aa52f31103830d74dcb5))

* sharing cache between region because wont cause conflict because db naming proof ([`c237478`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/c2374786e56a2bbd1bbc3ae285aa05c70ede8881))

* add premission for release ([`944c94f`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/944c94f132914c1305aaf3693508eb2139b905ad))

* update tagging workflow ([`d52c992`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/d52c99211349abbae4166690406b70f5a0f6488a))

* update tagging workflow ([`b726284`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/b7262841808be863bfa570e5760e3a663e2fc77c))

* update tagging workflow ([`b7f7825`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/b7f7825c0a544dbe72ef42391d83cf73948c0a99))

* auto tag latest on main ([`2603dbc`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2603dbc5e1e8d591a21a2857514c5284bd888d2b))

* update secret passing ([`e69744f`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e69744f97d913ac4347952481af3cc28fc14de34))

* update secret passing ([`9deb6cc`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9deb6ccb847c23be8103a73f90e35e6bacdee6f9))

* update secret passing ([`116d401`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/116d4013c1a54d87c3f43a5e5be2abc6af267a73))

* fix split line error in job.yml ([`8282b20`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/8282b200d73db3c126bf2993b0fecfbf9908593f))

* add tigger for update &amp; export action, rename coverage test action ([`f9404ab`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/f9404ab35da0b72dfe9e2a12af8f81282f482080))

* fix syntax error in job.yml ([`2499986`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2499986078cd179cca8b9047b313fb1f31863e90))

* fix syntax error in job.yml ([`e3f411c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/e3f411c2cb58eb96eeb8e425432bfcbd119f1d58))

* remove default value for compression ([`28e99ac`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/28e99ac7a12b67f9a9c4cba34a3e7a65a16d2ef9))

* add realm name to export, update tests ([`158da2c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/158da2c22c60a3e5817e1d04b0ad86951e442893))

* Few changes:
 - add argparse for main
 - figure out the default &#39;empty&#39; return value for numeric field in the exporter and when to skip a export record
 - fix bugs in the &#39;recent&#39; fields by adding timestamp check
 - update tests ([`9e08309`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9e0830940e4be1df1c03f190abe4154bf6735842))

* add caching for pip in cicd ([`75caf0b`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/75caf0b7fce76d8609374bfd53668bd0da32dadf))

* trigger ci ([`84eafdb`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/84eafdb327b072a4c8a10105e78bc1cf490ceb55))

* trigger ci ([`48a04a6`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/48a04a6081ddee4b7f109bb33771af16d3d21334))

* Update python-app.yml ([`30b05b3`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/30b05b3165fa1f9038a7c253c190cf7f3bca4d67))

* Fix unittest
newline auto-translate cause \n becomes \r\n in windows, leading to checksum difference. ([`363da3c`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/363da3cd275e4ca0bb8e672271d0fdcfb093f722))

* Print out export content
&#39;its working on my machine&#39; ([`9aeb295`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/9aeb2951aeba3e52d1db2e46ba6319a2bde38aaf))

* fix reading env ([`0d975a5`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/0d975a5b7369e743d11a77ec5201092f5ded9eca))

* update requirements ([`2f487a8`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/2f487a8294f9319be01bd98c0b2ac3adba9345d8))

* add requirement file ([`746e8da`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/746e8da19bad122d0bfb4cdfc8e5d6c3863628be))

* init ([`109f181`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/109f181606c321d228efe9802e88ca66fb0a8d09))

* Create python-app.yml ([`1fc6c0b`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/1fc6c0b08266e7c0d1d0db6fef083c13d3559841))

* Initial commit ([`dd44dbc`](https://github.com/kamoo1/Kamoo-s-TSM-App/commit/dd44dbced6056c790cc669dcbacb9d11848adc32))
