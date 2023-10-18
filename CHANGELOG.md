# CHANGELOG



## v0.1.0 (2023-10-18)

### Breaking

* feat: hc support and big refactor

BREAKING CHANGE: meta schema changed ([`57df47b`](https://github.com/kamoo1/TSM-Backend/commit/57df47bb9c020fe76e3076d497c17b390e708580))

* feat: batch patch

BREAKING CHANGE: removed `patch_tsm`, `--src_digest` now is a file. ([`6ab6206`](https://github.com/kamoo1/TSM-Backend/commit/6ab620670e6ab4482e62ef4867289f84741c9c8a))

* fix: remove the hacky export realm fix

BREAKING CHANGE: some new realms need `LibRealmInfo` patched to work. ([`9298fa2`](https://github.com/kamoo1/TSM-Backend/commit/9298fa262fd74bf003f69a8949d2afd5b78e8770))

### Chore

* chore: update locales ([`ba1afe4`](https://github.com/kamoo1/TSM-Backend/commit/ba1afe48df11b0751ae407ba4612411edee873b3))

* chore: update `bonuses_curves.json` ([`f112cb7`](https://github.com/kamoo1/TSM-Backend/commit/f112cb76349056673babf0bd0ec90d76a7118dd7))

* chore: improve logging, add comment ([`2b52055`](https://github.com/kamoo1/TSM-Backend/commit/2b52055656638383dd283dff02c83da86b6d957c))

* chore: remove unused comment ([`0c608a1`](https://github.com/kamoo1/TSM-Backend/commit/0c608a160737ca86e3054b11cadba60478efb6c3))

* chore: ocd ([`4d16a20`](https://github.com/kamoo1/TSM-Backend/commit/4d16a20df4538e366ddc83274f3dc0cbc35b462a))

* chore: add patch for `LibRealmInfo` ([`0f8798e`](https://github.com/kamoo1/TSM-Backend/commit/0f8798e909b194cca5b1e7d47b1c7080ddf6af98))

* chore: add translation ([`1878ff3`](https://github.com/kamoo1/TSM-Backend/commit/1878ff318bf2a2fedce7317c31658bd654f503d4))

* chore: add patch success log ([`0c159c1`](https://github.com/kamoo1/TSM-Backend/commit/0c159c1302145e42e6a39ea6a466f41591fff739))

* chore: update requirements &amp; coverage, add typing ([`4a088ea`](https://github.com/kamoo1/TSM-Backend/commit/4a088eacd1f76f42dc58173e9d1af7a9565fd759))

### Ci

* ci: add scripts ([`e390a14`](https://github.com/kamoo1/TSM-Backend/commit/e390a145e6c6c694f9122134059eb1801cd28503))

* ci: add automatic release ([`07d0edd`](https://github.com/kamoo1/TSM-Backend/commit/07d0edd903c3252f0b9e932554f3745ff624380a))

### Feature

* feat: client auto update

also migrates to `pydantic` 2.x ([`86da0a8`](https://github.com/kamoo1/TSM-Backend/commit/86da0a872ced0e5ad63592fe4042193c40b5615e))

* feat: add backward compatibility for `Meta` files ([`54c0efe`](https://github.com/kamoo1/TSM-Backend/commit/54c0efef592294ad4b5054c47ea618b51ffa4bc5))

* feat: add system info collector for `Meta` ([`9a802f1`](https://github.com/kamoo1/TSM-Backend/commit/9a802f105b68a6aca73944367a20a1658a3648f0))

* feat: add entrypoint for binary release ([`e9113c3`](https://github.com/kamoo1/TSM-Backend/commit/e9113c33ba7db4b150445d0cdeb3641dd5113362))

* feat: UI

- finishing up internationalization, patching
- fixed few bugs
- refactored entry point for binary release ([`96b4d90`](https://github.com/kamoo1/TSM-Backend/commit/96b4d904371bd4f7fdd0afdaa1a36a41efafed57))

* feat: UI

WIP:
add LibRealmInfo patching
localization support ([`8dcec5e`](https://github.com/kamoo1/TSM-Backend/commit/8dcec5ec5112c2eb7b3aca459a5d1ae7571af55a))

* feat: add text file patcher ([`4be74eb`](https://github.com/kamoo1/TSM-Backend/commit/4be74ebe63ca12fae20cbdae15c30c4258660eaf))

### Fix

* fix: few bugs

fix meta bug where unable to label HC for non en_US requests
fix UI bug where widgets gets incorrectly enabled / disabled
fix UI update always take remote mode
improve logging / supress ssl warning ([`a246a3e`](https://github.com/kamoo1/TSM-Backend/commit/a246a3e5e076588a9861ef683a8c32a347180407))

* fix: regional price sources were unsorted ([`2f1799c`](https://github.com/kamoo1/TSM-Backend/commit/2f1799c9ecc7df3fbe58a8a9c9d660af90fb9f28))

* fix: random SSL cert error, improve error handling

- ignoring ssl verification due to random SSL cert expire error.
- auctions schema now accepts optional `auctions` field.
- more explicit request error handling ([`4e676cb`](https://github.com/kamoo1/TSM-Backend/commit/4e676cb210a33552aadce1f181b4955e3e11f087))

* fix: mock warcraft path during testing ([`b44fa0d`](https://github.com/kamoo1/TSM-Backend/commit/b44fa0d44bf46f9793b3994c7f1154ebda06e3db))

* fix: running without data

many routines of this project doesn&#39;t depend on `bonuses_courves.json`,
make it so it&#39;s able to run them without it. ([`4093659`](https://github.com/kamoo1/TSM-Backend/commit/4093659980855648b3cd7fed52a867571cfea7da))

* fix: ui freezes while having connection issues

tone down the `backoff_factor` in `GHAPI` ([`59083fd`](https://github.com/kamoo1/TSM-Backend/commit/59083fdcdbd5cb79855044412741ac570bfddcb0))

### Test

* test: roll back ilvl test change

will re-apply after we update `bonuses_courves.json` later ([`6d52bfd`](https://github.com/kamoo1/TSM-Backend/commit/6d52bfd6d6b8a5dbbc3ef04730e47ff71b05749a))

* test: add test for `Meta` ([`273b578`](https://github.com/kamoo1/TSM-Backend/commit/273b5785c62724c450ec98d62b1527ddab105126))

### Unknown

* Merge pull request #39 from kamoo1/dev

Dev ([`5450d73`](https://github.com/kamoo1/TSM-Backend/commit/5450d736cfd92d2821c1a8b18280efd38296e2da))

* Merge branch &#39;main&#39; into dev ([`b396c65`](https://github.com/kamoo1/TSM-Backend/commit/b396c65cd4f9f83317eace3fa84d20acc773210d))

* Merge pull request #38 from kamoo1/ui

Feat: UI ([`f41028a`](https://github.com/kamoo1/TSM-Backend/commit/f41028ae83cb809e3e63c14f19a374b1a3de8d1c))

* doc: update readme ([`3082fbd`](https://github.com/kamoo1/TSM-Backend/commit/3082fbdafd4859a35aaed0bd0e4441a13bf9e957))

* WIP: UI ([`4288789`](https://github.com/kamoo1/TSM-Backend/commit/4288789e472ec407943f58eb260cfa13da1d8acb))

* Safety Measure for Python 3.10 `StrEnum` ([`bd56577`](https://github.com/kamoo1/TSM-Backend/commit/bd56577ca41bd1a9896f4ce5860d07a960fb9da5))

* Remove Useless Comment ([`3720f2d`](https://github.com/kamoo1/TSM-Backend/commit/3720f2d702feb32d4fac384e0c0283f5e52712ef))

* WIP: UI ([`c42f309`](https://github.com/kamoo1/TSM-Backend/commit/c42f309bd060df24d858ce979e8b94393304ba73))

* Update Tests ([`4773cf0`](https://github.com/kamoo1/TSM-Backend/commit/4773cf0501c424f1d2120a66cfd218b442bdc0af))

* Add Traceback for `DownloadError` Warning ([`fa1a1c0`](https://github.com/kamoo1/TSM-Backend/commit/fa1a1c0416cf3286770a8da6f67de57d9b06d356))

* Improve:
 - Clarify logic of some optional parameters
 - Add `--repo` and `--gh_proxy` options, allowing &#34;remote + local&#34; mode
 - Decrease logging level of failed auction requests to &#34;warning&#34;. ([`5a41e88`](https://github.com/kamoo1/TSM-Backend/commit/5a41e880c3c49baedbf36698a75be57a5020f7c8))

* Improve:
 - Clarify logic of some optional parameters
 - Apply recently added validators to argument parser ([`a9bd13b`](https://github.com/kamoo1/TSM-Backend/commit/a9bd13bfc55976bf276ef91daa0d095a9248a8cd))

* Improvements:
 - Use custom `DownloadError` to indicate expected downloading errors.
 - Display them as warnings instead of errors.
 - DB mode variable naming change ([`9e11a26`](https://github.com/kamoo1/TSM-Backend/commit/9e11a262c25b45e951ec30d46fb077c17da31494))

* Validate GH Proxy Scheme ([`0277561`](https://github.com/kamoo1/TSM-Backend/commit/0277561752b2ff2d327c92845e2480f7d9fe5798))

* Improve Logging ([`9e69842`](https://github.com/kamoo1/TSM-Backend/commit/9e6984240afcfe07100ee0683a1e15bea6f125a3))

* Update Requirements ([`0f3cc5f`](https://github.com/kamoo1/TSM-Backend/commit/0f3cc5f92b5b07d06cc7665bc4716306f836c7fe))

* WIP: UI Feature ([`119c375`](https://github.com/kamoo1/TSM-Backend/commit/119c375693a2e478049281e13363fce6abe9eb66))

* Changes:
 - Add Warcraft bases path validation
 - Some minor changes ([`3d76027`](https://github.com/kamoo1/TSM-Backend/commit/3d7602788c2b75eadc1590e7947b5cf8451ac9a6))

* Overload `load_meta`, allow `Namespace`. ([`619d6b5`](https://github.com/kamoo1/TSM-Backend/commit/619d6b506f47627fdebdc9c8ac9beb0c49bb3d18))

* Changes:
 - fix URL tailing slash issue
 - add URL validation ([`e3b9740`](https://github.com/kamoo1/TSM-Backend/commit/e3b974002c93a771caed1dec3603ef0fdcce31f2))

* Support Python3.11 Breaking Change
Fixes #37 ([`e20b58d`](https://github.com/kamoo1/TSM-Backend/commit/e20b58dc15a2822d667f64e235813dd88b0bf49d))

* Standardize Import Statement ([`8362203`](https://github.com/kamoo1/TSM-Backend/commit/836220311a9254a2deb4a6ea7f7431639390ff63))

* Tune Down GHAPI Cache TTL ([`f6e85bc`](https://github.com/kamoo1/TSM-Backend/commit/f6e85bc316be7f5f1c9c7e318aba5049c4bad4d0))

* Merge pull request #35 from kamoo1/dev

Remove Parallelism ([`ed53ef5`](https://github.com/kamoo1/TSM-Backend/commit/ed53ef5e09ab7fe13530bcb8af37b685ac56a786))

* Remove Parallelism
There&#39;s a issue that happens by chance when multiple access tokens are used in parallel (i think?). ([`2638bb5`](https://github.com/kamoo1/TSM-Backend/commit/2638bb5439670d93d1adc262a7659f87992a26ff))

* Merge pull request #34 from kamoo1/dev

Update Housekeeping Script ([`6da0e07`](https://github.com/kamoo1/TSM-Backend/commit/6da0e0723117cbfc4485d8692ae722c276c6ec2e))

* Update Housekeeping Script
Remove bad classic data ([`e62e16f`](https://github.com/kamoo1/TSM-Backend/commit/e62e16f34e038a74915e384138fffe33ba6de32e))

* Merge pull request #33 from kamoo1/dev

Correct Classic Prices ([`f466342`](https://github.com/kamoo1/TSM-Backend/commit/f46634283b546c883cd68ca5981cbf9b02651c7d))

* Correct Classic Prices ([`0177963`](https://github.com/kamoo1/TSM-Backend/commit/0177963e80e885684e96e5020e6ad25637d09681))

* Correct Classic Prices ([`a75de9d`](https://github.com/kamoo1/TSM-Backend/commit/a75de9dc12d1a4ea6f640fdb9f33eb2d9bb7b9b4))

* Merge pull request #32 from kamoo1/dev

oppsie ([`49777e6`](https://github.com/kamoo1/TSM-Backend/commit/49777e6ffd49d635e440a6e39b72eeeb83a4a3c7))

* Merge branch &#39;main&#39; into dev ([`273f37c`](https://github.com/kamoo1/TSM-Backend/commit/273f37cd9e7bebcaa126256ce25bc5a7f981c260))

* oppsie ([`cfaea0f`](https://github.com/kamoo1/TSM-Backend/commit/cfaea0f18b9a9ccdf3f47b937b34110e59c67a56))

* Merge pull request #31 from kamoo1/dev

Dev ([`7170019`](https://github.com/kamoo1/TSM-Backend/commit/717001909b9914b13fff667b0e579b2376e2a8d6))

* Update Readme ([`4fe1491`](https://github.com/kamoo1/TSM-Backend/commit/4fe14915e46fedb725b38bcdff7df01e51d6f525))

* Add Korean Region to Update Schedule ([`59bc52c`](https://github.com/kamoo1/TSM-Backend/commit/59bc52c27c7353e62b3ce12e276104a3a9330530))

* Merge pull request #30 from kamoo1/dev

Dev ([`6581005`](https://github.com/kamoo1/TSM-Backend/commit/6581005e1be9199cefa1b726e7874b76c700de50))

* Parallelize Github Workflow
I&#39;ll blame it on Bing if it explodes ([`30f622c`](https://github.com/kamoo1/TSM-Backend/commit/30f622c5aac3d8b3a900ca0fb8a694540758324e))

* Update Housekeeping Script
I changed the naming yet again :) ([`f0b7e0c`](https://github.com/kamoo1/TSM-Backend/commit/f0b7e0ce22a856ea837a50e1f2a368e3b995bbf7))

* Support Arbitrary Number of Assets ([`df181ad`](https://github.com/kamoo1/TSM-Backend/commit/df181ad12cee3847ae183c05e60af909242e6f82))

* Fix Retail Export ([`cd641ae`](https://github.com/kamoo1/TSM-Backend/commit/cd641ae0fcd1206746b2acbcb02c5c856f257e9c))

* Update Readme ([`f43a8be`](https://github.com/kamoo1/TSM-Backend/commit/f43a8be4bf1d4fc91c622daa0c8691023b5ad901))

* Update Comment ([`97ff125`](https://github.com/kamoo1/TSM-Backend/commit/97ff1254aba46d3f529ca842caa4cc600961ac3d))

* Add Classic Support ([`3708169`](https://github.com/kamoo1/TSM-Backend/commit/3708169a5b12b8db9deef6cd08924ab07c41f08f))

* Merge pull request #29 from kamoo1/dev

Migrate Internal Models to Attrs ([`7838347`](https://github.com/kamoo1/TSM-Backend/commit/7838347f77ea604cbb60a135726de6ab219090e3))

* Merge branch &#39;main&#39; into dev ([`0e7d4ca`](https://github.com/kamoo1/TSM-Backend/commit/0e7d4ca58ea82daac57850bc81d738d1cb77f580))

* Migrate Internal Models to Attrs ([`4bc03f6`](https://github.com/kamoo1/TSM-Backend/commit/4bc03f6c645e6ffb1f65512e085cdaf6e26da52e))

* Merge pull request #28 from kamoo1/dev

Dev ([`5b3a9b7`](https://github.com/kamoo1/TSM-Backend/commit/5b3a9b7af99cf4561fe59ad4877c151080b374a7))

* Update Readme ([`674a88e`](https://github.com/kamoo1/TSM-Backend/commit/674a88e71cdaee9f987de8553a0aec88eac488a0))

* Add Records Compression:
Compress records since yesterday, into aggregated daily results ([`257f530`](https://github.com/kamoo1/TSM-Backend/commit/257f5302145d6effe87f0adf26af16ef26f5044c))

* Correct Exception Message ([`4f295e2`](https://github.com/kamoo1/TSM-Backend/commit/4f295e22723f534dba41810b45afff015e87b9dd))

* Add Retry and GHProxy to GHAPI ([`bd8bc45`](https://github.com/kamoo1/TSM-Backend/commit/bd8bc458c0f80dec668113ff18aaaed4ed5f1d2f))

* Format Error Messages ([`ece70e7`](https://github.com/kamoo1/TSM-Backend/commit/ece70e74d544201b919c7007614b752fcd6274bb))

* Merge pull request #27 from kamoo1/dev

Dev ([`25247ce`](https://github.com/kamoo1/TSM-Backend/commit/25247ceed289a67c78649d29e92dd338eab8f98f))

* Update Housekeeping Script ([`e0062a5`](https://github.com/kamoo1/TSM-Backend/commit/e0062a5fa35c0d90dd8f2e3d1e72568f3542fb96))

* Revert &#34;Keep Empty Game Version in File Name&#34;

This reverts commit 317d08c5cb48ff952af87597cd9ae6f9d6ed322c. ([`6b6329a`](https://github.com/kamoo1/TSM-Backend/commit/6b6329a0869fd675f1ca3890b98f2694fce2008b))

* Merge pull request #26 from kamoo1/dev

Releasing All JSON Files Under Output ([`66140db`](https://github.com/kamoo1/TSM-Backend/commit/66140db48f338befaefde8ec77b5623d4808f641))

* Releasing All JSON Files Under Output ([`6c70d50`](https://github.com/kamoo1/TSM-Backend/commit/6c70d506ec43dee4d48a5e17bd83a2f47395b7e7))

* Merge pull request #25 from kamoo1/dev

Add Housekeeping Script ([`0cb5ee2`](https://github.com/kamoo1/TSM-Backend/commit/0cb5ee2966dab1f1af38f5f3e6860aa50fe82da0))

* Add Housekeeping Script ([`842a92e`](https://github.com/kamoo1/TSM-Backend/commit/842a92ef1cc0f386d300fe9f3bf79f506ccf9a75))

* Merge pull request #24 from kamoo1/dev

Add Housekeeping Script ([`3cd92bb`](https://github.com/kamoo1/TSM-Backend/commit/3cd92bbef4765df128c5f1252f6e5720fe55385a))

* Merge branch &#39;main&#39; into dev ([`6a39e0e`](https://github.com/kamoo1/TSM-Backend/commit/6a39e0ee26bf213dc3e6db9cf887243292619de0))

* Add Housekeeping Script ([`d2599f2`](https://github.com/kamoo1/TSM-Backend/commit/d2599f2895fc6707e0becfa6fe0da7383c3eff20))

* Merge pull request #23 from kamoo1/dev

Dev ([`1cd8f8a`](https://github.com/kamoo1/TSM-Backend/commit/1cd8f8a331cec0f09ff3119ae39c02bb6c2d68cd))

* Add Housekeeping Script and Job ([`ff036e6`](https://github.com/kamoo1/TSM-Backend/commit/ff036e6984ac972262db7cac7a473ebf47d47bb1))

* Add Housekeeping Script and Job ([`f62409c`](https://github.com/kamoo1/TSM-Backend/commit/f62409c2f2e1ae7315f0544600889b1be09d54f5))

* Keep Empty Game Version in File Name ([`317d08c`](https://github.com/kamoo1/TSM-Backend/commit/317d08c5cb48ff952af87597cd9ae6f9d6ed322c))

* Update Readme
Add roadmap ([`c01cb66`](https://github.com/kamoo1/TSM-Backend/commit/c01cb6650900f610f3033d7fd560cb3efead6f3c))

* Game Version Basic Support ([`2e16774`](https://github.com/kamoo1/TSM-Backend/commit/2e1677409e7aab3d4c6a24deb8d1ef1c61cc400d))

* Rename TaskManager to Updater ([`204a67a`](https://github.com/kamoo1/TSM-Backend/commit/204a67a53477557f71ad6bdaf8b16d4fb90c00d3))

* Merge pull request #22 from kamoo1/dev

Dev ([`04f1ce3`](https://github.com/kamoo1/TSM-Backend/commit/04f1ce33462f9d2372a3de694816ad030e15fe9d))

* Add AH Update Badge ([`062aed3`](https://github.com/kamoo1/TSM-Backend/commit/062aed392dd4e1b961b99308921b94ef3a43841b))

* Remove Deprecated Option ([`68239fd`](https://github.com/kamoo1/TSM-Backend/commit/68239fdd883b3d18c18a8a45ca392b01332b1cff))

* Fix Export Data:
&#39;AUCTIONDB_REALM_HISTORICAL&#39; and &#39;AUCTIONDB_REALM_SCAN_STAT&#39; should also contain commodities data ([`9c42698`](https://github.com/kamoo1/TSM-Backend/commit/9c42698add27c8c4e2cf9e2b58113a4b55573cf5))

* Merge pull request #21 from kamoo1/dev

Dev ([`8f7dad1`](https://github.com/kamoo1/TSM-Backend/commit/8f7dad13fde11f453303dc4e5c49c8996950a4e9))

* Make Exceptions Meaningful ([`ed994a0`](https://github.com/kamoo1/TSM-Backend/commit/ed994a077e9c36f37508689aeb3693fbd7638109))

* Correct Arguments for Exporter:
At least one realm should be given ([`bc2e5fd`](https://github.com/kamoo1/TSM-Backend/commit/bc2e5fd8005d461ea523ff5ade00ce4a84a20d99))

* Simplify Command Line Args:
 - Adding default value for DB path
 - Update related command in README ([`c743d31`](https://github.com/kamoo1/TSM-Backend/commit/c743d31e3caf6ac9a00216715ba29b1b1d05197f))

* Merge pull request #20 from kamoo1/dev

Dev ([`fc16a67`](https://github.com/kamoo1/TSM-Backend/commit/fc16a670e93fcea3fd8cd462a3313998bdf50d83))

* Merge branch &#39;main&#39; into dev ([`949f2ae`](https://github.com/kamoo1/TSM-Backend/commit/949f2ae3fedb6739bff36cc26bcf55bd187121b6))

* Update `requirements.txt` ([`d79c214`](https://github.com/kamoo1/TSM-Backend/commit/d79c21436b338b00232fc8706a42d561a0b44998))

* Update README ([`c73bd9a`](https://github.com/kamoo1/TSM-Backend/commit/c73bd9a8519cc267bfd96b128f36b735b2e834c6))

* Changes:
 - rename `task_manager.py` to `updater.py`
 - move updater&#39;s entry to `ah.updater` ([`9a81908`](https://github.com/kamoo1/TSM-Backend/commit/9a81908ff109cc65e76fee4f23d7567fe48f6a3c))

* Meta Data:
 - add connected realms info so we don&#39;t have to use battle net api when exporting;
 - gathering some basic system info;

Exporter:
 - add argparse ([`a79450d`](https://github.com/kamoo1/TSM-Backend/commit/a79450df80e7b1b3e07278dda561f91410d94f6d))

* Merge pull request #19 from kamoo1/dev

add support for ilvl items in ItemString ([`96054b2`](https://github.com/kamoo1/TSM-Backend/commit/96054b2f367d86c981c10760bc35a7dc7c9e971b))

* add support for ilvl items in ItemString ([`520eb0d`](https://github.com/kamoo1/TSM-Backend/commit/520eb0de1bac95d556df052dfcffcb8827248355))

* Merge pull request #18 from kamoo1/dev

Dev ([`001018e`](https://github.com/kamoo1/TSM-Backend/commit/001018e12c90073c06357524bdb45740f322deff))

* Merge branch &#39;main&#39; into dev ([`0166b66`](https://github.com/kamoo1/TSM-Backend/commit/0166b6600bc459862fa6815fcc4b58039ca5356a))

* forgot to save few properties in protobuf of map records ([`bdbb61f`](https://github.com/kamoo1/TSM-Backend/commit/bdbb61fe64aee41b10ea6f77712e3c3ab181d5fc))

* wip: some updates ([`4aa989a`](https://github.com/kamoo1/TSM-Backend/commit/4aa989afa052c16a4fecbd96064a7bd853190c38))

* add more unittest, some improve on code ([`09a9659`](https://github.com/kamoo1/TSM-Backend/commit/09a96592b9fe2113bd05fc40a175b268b64879b9))

* allowing db using remote file`nfinishing up export`nWIP: test ([`68eaaa4`](https://github.com/kamoo1/TSM-Backend/commit/68eaaa48e5cf3e9dfee5c8bb1b31a4177584414b))

* Merge pull request #17 from kamoo1/dev

also release meta file ([`7a65720`](https://github.com/kamoo1/TSM-Backend/commit/7a6572026352a9384a8818c34b1aded851675a30))

* Merge branch &#39;main&#39; into dev ([`f44ef0b`](https://github.com/kamoo1/TSM-Backend/commit/f44ef0b6bc17cf5b6b450c3368afa446033f1928))

* also release meta file ([`e3e65f2`](https://github.com/kamoo1/TSM-Backend/commit/e3e65f250cdf09efe31068103842cca51bd11c85))

* Merge pull request #16 from kamoo1/dev

Dev ([`2bbbffa`](https://github.com/kamoo1/TSM-Backend/commit/2bbbffa0eadb884c811272b7bc33c94f94c5334f))

* refactoring code, export is in WIP ([`9c3c42d`](https://github.com/kamoo1/TSM-Backend/commit/9c3c42d85375dd259fb6e3c0673ef4c12c14ac16))

* update job display name ([`c7d00df`](https://github.com/kamoo1/TSM-Backend/commit/c7d00df0eb17d07b2c395416ea374f29364ad89f))

* Merge pull request #15 from kamoo1/dev

Dev ([`9858bdf`](https://github.com/kamoo1/TSM-Backend/commit/9858bdfe38b4d92a157f94177f7d858980e6f548))

* release db files instead ([`5d78144`](https://github.com/kamoo1/TSM-Backend/commit/5d781447eabab63a57ccb5a16a9318b006db52f4))

* Changes:`n - pet id should be pet_species_id`n - remove unnessary parameter in from_response ([`85190f0`](https://github.com/kamoo1/TSM-Backend/commit/85190f0290563152415e975b8dabb281c33b2f56))

* add warps ([`2b80db3`](https://github.com/kamoo1/TSM-Backend/commit/2b80db3544f2a31e6834aff0a901ece6eb8ad18c))

* use default locale for realm name that is supported by TSM ([`e7260b0`](https://github.com/kamoo1/TSM-Backend/commit/e7260b03f5c44a3d71780696bd30e60f40a3e69b))

* Merge pull request #14 from kamoo1/dev

Dev ([`05ae501`](https://github.com/kamoo1/TSM-Backend/commit/05ae50150f439621e83bbb6aeef29246ca27b469))

* update tests ([`b67a494`](https://github.com/kamoo1/TSM-Backend/commit/b67a49496d433ded4cdb0011850285c20db6da5c))

* add badge ([`3a9671b`](https://github.com/kamoo1/TSM-Backend/commit/3a9671be29246e08eb014e1935a0704c198de481))

* change log level warning-&gt;debug for empty export rows ([`104bc1d`](https://github.com/kamoo1/TSM-Backend/commit/104bc1df6f90b65acd568aec29cc7cb4d072c331))

* tidy up ([`9074fc4`](https://github.com/kamoo1/TSM-Backend/commit/9074fc4ab4db0f8dd6f1d7822a55b7b66ef121ac))

* Merge pull request #13 from kamoo1/dev

update readme ([`6ab78d3`](https://github.com/kamoo1/TSM-Backend/commit/6ab78d30600cb8444e26e52674014c59d528b552))

* update readme ([`dc36274`](https://github.com/kamoo1/TSM-Backend/commit/dc362740044f2e15104c78ba5a33d7b3143f4b04))

* Merge pull request #12 from kamoo1/dev

merge dev to main ([`d20e7e3`](https://github.com/kamoo1/TSM-Backend/commit/d20e7e327e271cc41f1ca8c4040433745abe220f))

* add readme ([`0322d56`](https://github.com/kamoo1/TSM-Backend/commit/0322d56d5d5299ebe211aa52f31103830d74dcb5))

* sharing cache between region because wont cause conflict because db naming proof ([`c237478`](https://github.com/kamoo1/TSM-Backend/commit/c2374786e56a2bbd1bbc3ae285aa05c70ede8881))

* Merge pull request #11 from kamoo1/dev

add premission for release ([`d5f0bab`](https://github.com/kamoo1/TSM-Backend/commit/d5f0baba81476d82a6e16594f1158321d3d9034c))

* add premission for release ([`944c94f`](https://github.com/kamoo1/TSM-Backend/commit/944c94f132914c1305aaf3693508eb2139b905ad))

* Merge pull request #10 from kamoo1/dev

checkout latest tag in the job ([`3757ac2`](https://github.com/kamoo1/TSM-Backend/commit/3757ac27dcf4928cfc5bff49dba8120fc794aa35))

* checkout latest tag in the job ([`33a5abb`](https://github.com/kamoo1/TSM-Backend/commit/33a5abbfc42284d55a189bc6d99b28fe10437cab))

* Merge pull request #9 from kamoo1/dev

update tagging workflow ([`e2203e0`](https://github.com/kamoo1/TSM-Backend/commit/e2203e08cff905eacdf2c42ffaa22df55d787ba9))

* update tagging workflow ([`d52c992`](https://github.com/kamoo1/TSM-Backend/commit/d52c99211349abbae4166690406b70f5a0f6488a))

* Merge pull request #8 from kamoo1/dev

update tagging workflow ([`3409f4e`](https://github.com/kamoo1/TSM-Backend/commit/3409f4e5ee76c8ad3104bd18aab80b06adf7eaf2))

* update tagging workflow ([`b726284`](https://github.com/kamoo1/TSM-Backend/commit/b7262841808be863bfa570e5760e3a663e2fc77c))

* Merge pull request #7 from kamoo1/dev

update tagging workflow ([`6f3405f`](https://github.com/kamoo1/TSM-Backend/commit/6f3405fe55c6bb87fb31f5872cbca7733b69c56c))

* update tagging workflow ([`b7f7825`](https://github.com/kamoo1/TSM-Backend/commit/b7f7825c0a544dbe72ef42391d83cf73948c0a99))

* Merge pull request #6 from kamoo1/dev

auto tag latest on main ([`e957be7`](https://github.com/kamoo1/TSM-Backend/commit/e957be71391687c5f48ada3ad51965716c22f508))

* auto tag latest on main ([`2603dbc`](https://github.com/kamoo1/TSM-Backend/commit/2603dbc5e1e8d591a21a2857514c5284bd888d2b))

* Merge pull request #5 from kamoo1/dev

update secret passing ([`53f60c9`](https://github.com/kamoo1/TSM-Backend/commit/53f60c9715a0aeec7da1fd0fa86d8b26e38ae8d0))

* update secret passing ([`e69744f`](https://github.com/kamoo1/TSM-Backend/commit/e69744f97d913ac4347952481af3cc28fc14de34))

* Merge pull request #4 from kamoo1/dev

merge dev to main ([`bd7513d`](https://github.com/kamoo1/TSM-Backend/commit/bd7513d313cc25178afe31adfb7676b79626432c))

* update secret passing ([`9deb6cc`](https://github.com/kamoo1/TSM-Backend/commit/9deb6ccb847c23be8103a73f90e35e6bacdee6f9))

* update secret passing ([`116d401`](https://github.com/kamoo1/TSM-Backend/commit/116d4013c1a54d87c3f43a5e5be2abc6af267a73))

* Merge pull request #3 from kamoo1/dev

Merge dev to main ([`4f03407`](https://github.com/kamoo1/TSM-Backend/commit/4f0340772cd4eaf55160c22f0e88414f926439ca))

* fix split line error in job.yml ([`8282b20`](https://github.com/kamoo1/TSM-Backend/commit/8282b200d73db3c126bf2993b0fecfbf9908593f))

* add tigger for update &amp; export action, rename coverage test action ([`f9404ab`](https://github.com/kamoo1/TSM-Backend/commit/f9404ab35da0b72dfe9e2a12af8f81282f482080))

* Merge pull request #2 from kamoo1/dev

Merge dev to main ([`736a8d5`](https://github.com/kamoo1/TSM-Backend/commit/736a8d539f76381afcd41bbfb9fd677cc9a1db9c))

* fix syntax error in job.yml ([`2499986`](https://github.com/kamoo1/TSM-Backend/commit/2499986078cd179cca8b9047b313fb1f31863e90))

* fix syntax error in job.yml ([`e3f411c`](https://github.com/kamoo1/TSM-Backend/commit/e3f411c2cb58eb96eeb8e425432bfcbd119f1d58))

* Merge pull request #1 from kamoo1/dev

merge dev to main ([`4817989`](https://github.com/kamoo1/TSM-Backend/commit/4817989f5ecadd236cad97daa03672d8cb85aa9c))

* test out serverless action ([`e13f9e3`](https://github.com/kamoo1/TSM-Backend/commit/e13f9e3256b2986837dfd82e5ffdf31271c28a0d))

* remove default value for compression ([`28e99ac`](https://github.com/kamoo1/TSM-Backend/commit/28e99ac7a12b67f9a9c4cba34a3e7a65a16d2ef9))

* add realm name to export, update tests ([`158da2c`](https://github.com/kamoo1/TSM-Backend/commit/158da2c22c60a3e5817e1d04b0ad86951e442893))

* Few changes:
 - add argparse for main
 - figure out the default &#39;empty&#39; return value for numeric field in the exporter and when to skip a export record
 - fix bugs in the &#39;recent&#39; fields by adding timestamp check
 - update tests ([`9e08309`](https://github.com/kamoo1/TSM-Backend/commit/9e0830940e4be1df1c03f190abe4154bf6735842))

* add caching for pip in cicd ([`75caf0b`](https://github.com/kamoo1/TSM-Backend/commit/75caf0b7fce76d8609374bfd53668bd0da32dadf))

* trigger ci ([`84eafdb`](https://github.com/kamoo1/TSM-Backend/commit/84eafdb327b072a4c8a10105e78bc1cf490ceb55))

* trigger ci ([`48a04a6`](https://github.com/kamoo1/TSM-Backend/commit/48a04a6081ddee4b7f109bb33771af16d3d21334))

* Update python-app.yml ([`30b05b3`](https://github.com/kamoo1/TSM-Backend/commit/30b05b3165fa1f9038a7c253c190cf7f3bca4d67))

* Fix unittest
newline auto-translate cause \n becomes \r\n in windows, leading to checksum difference. ([`363da3c`](https://github.com/kamoo1/TSM-Backend/commit/363da3cd275e4ca0bb8e672271d0fdcfb093f722))

* Print out export content
&#39;its working on my machine&#39; ([`9aeb295`](https://github.com/kamoo1/TSM-Backend/commit/9aeb2951aeba3e52d1db2e46ba6319a2bde38aaf))

* fix reading env ([`0d975a5`](https://github.com/kamoo1/TSM-Backend/commit/0d975a5b7369e743d11a77ec5201092f5ded9eca))

* update requirements ([`2f487a8`](https://github.com/kamoo1/TSM-Backend/commit/2f487a8294f9319be01bd98c0b2ac3adba9345d8))

* add requirement file ([`746e8da`](https://github.com/kamoo1/TSM-Backend/commit/746e8da19bad122d0bfb4cdfc8e5d6c3863628be))

* init ([`109f181`](https://github.com/kamoo1/TSM-Backend/commit/109f181606c321d228efe9802e88ca66fb0a8d09))

* Create python-app.yml ([`1fc6c0b`](https://github.com/kamoo1/TSM-Backend/commit/1fc6c0b08266e7c0d1d0db6fef083c13d3559841))

* Initial commit ([`dd44dbc`](https://github.com/kamoo1/TSM-Backend/commit/dd44dbced6056c790cc669dcbacb9d11848adc32))
