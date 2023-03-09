"""wow_profile_api.py file."""
from ..api import Api


class WowProfileApi(Api):
    """All Wow Profile API methods.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init WowProfileApi."""
        super().__init__(client_id, client_secret)

    # Account Profile API

    def get_account_profile_summary(self, region, locale, access_token):
        """Return a profile summary for an account."""
        resource = "/profile/user/wow"
        query_params = {
            "namespace": f"profile-{region}",
            "locale": locale,
            "access_token": access_token,
        }
        return super().get_resource(resource, region, query_params)

    def get_protected_character_profile_summary(
        self, region, locale, access_token, realm_id, character_id
    ):
        """Return a protected profile summary for a character."""
        resource = f"/profile/user/wow/protected-character/{realm_id}-{character_id}"
        query_params = {
            "namespace": f"profile-{region}",
            "locale": locale,
            "access_token": access_token,
        }
        return super().get_resource(resource, region, query_params)

    def get_account_collections_index(self, region, locale, access_token):
        """Return an index of collection types for an account."""
        resource = "/profile/user/wow/collections"
        query_params = {
            "namespace": f"profile-{region}",
            "locale": locale,
            "access_token": access_token,
        }
        return super().get_resource(resource, region, query_params)

    def get_account_mounts_collection_summary(self, region, locale, access_token):
        """Return a summary of the mounts an account has obtained."""
        resource = "/profile/user/wow/collections/mounts"
        query_params = {
            "namespace": f"profile-{region}",
            "locale": locale,
            "access_token": access_token,
        }
        return super().get_resource(resource, region, query_params)

    def get_account_pets_collection_summary(self, region, locale, access_token):
        """Return a summary of the battle pets an account has obtained."""
        resource = "/profile/user/wow/collections/pets"
        query_params = {
            "namespace": f"profile-{region}",
            "locale": locale,
            "access_token": access_token,
        }
        return super().get_resource(resource, region, query_params)

    # Character Achievements API

    def get_character_achievements_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of the achievements a character has completed."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/achievements"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_achievement_statistics(
        self, region, locale, realm_slug, character_name
    ):
        """Return a character's statistics as they pertain to achievements."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/achievements/statistics"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Appearance API

    def get_character_appearance_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of a character's appearance settings."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/appearance"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Collections API

    def get_character_collections_index(
        self, region, locale, realm_slug, character_name
    ):
        """Return an index of collection types for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/collections"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_mounts_collection_index(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of the mounts a character has obtained."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/collections/mounts"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_pets_collection_index(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of the battle pets a character has obtained."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/collections/pets"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Encounters API

    def get_character_encounters_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of a character's encounters."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/encounters"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_dungeons(self, region, locale, realm_slug, character_name):
        """Return a summary of a character's completed dungeons."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/encounters/dungeons"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_raids(self, region, locale, realm_slug, character_name):
        """Return a summary of a character's completed raids."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/encounters/raids"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Equipment API

    def get_character_equipment_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of the items equipped by a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/equipment"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Hunter Pets API

    def get_character_hunter_pets_summary(
        self, region, locale, realm_slug, character_name
    ):
        """If the character is a hunter, returns a summary of the character's hunter pets."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/hunter-pets"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Media API

    def get_character_media_summary(self, region, locale, realm_slug, character_name):
        """Return a summary of the media assets available for a character (such as an avatar render)."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/character-media"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Mythic Keystone Profile API

    def get_character_mythic_keystone_profile_index(
        self, region, locale, realm_slug, character_name
    ):
        """Return the Mythic Keystone profile index for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/mythic-keystone-profile"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_mythic_keystone_profile_season_details(
        self, region, locale, realm_slug, character_name, season_id
    ):
        """Return the Mythic Keystone season details for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/mythic-keystone-profile/season/{season_id}"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Professions API

    def get_character_professions_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of professions for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/professions"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Profile API

    def get_character_profile_summary(self, region, locale, realm_slug, character_name):
        """Return a profile summary for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_profile_status(self, region, locale, realm_slug, character_name):
        """Return the status and a unique ID for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/status"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Pvp API

    def get_character_pvp_bracket_statistics(
        self, region, locale, realm_slug, character_name, pvp_bracket
    ):
        """Return the Pvp bracket statistics for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/pvp-bracket/{pvp_bracket}"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_pvp_summary(self, region, locale, realm_slug, character_name):
        """Return a Pvp summary for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/pvp-summary"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Quests API

    def get_character_quests(self, region, locale, realm_slug, character_name):
        """Return a character's active quests as well as a link to the character's completed quests."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/quests"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_character_completed_quests(
        self, region, locale, realm_slug, character_name
    ):
        """Return a list of quests that a character has completed."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/quests/completed"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Reputations API

    def get_character_reputations_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of a character's reputations."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/reputations"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Specializations API

    def get_character_specializations_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a summary of a character's specializations."""
        resource = (
            f"/profile/wow/character/{realm_slug}/{character_name}/specializations"
        )
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Statistics API

    def get_character_statistics_summary(
        self, region, locale, realm_slug, character_name
    ):
        """Return a statistics summary for a character."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/statistics"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Character Titles API

    def get_character_titles_summary(self, region, locale, realm_slug, character_name):
        """Return a summary of titles a character has obtained."""
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/titles"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    # Guild API

    def get_guild(self, region, locale, realm_slug, name_slug):
        """Return a single guild by its name and realm."""
        resource = f"/data/wow/guild/{realm_slug}/{name_slug}"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_guild_activity(self, region, locale, realm_slug, name_slug):
        """Return a single guild's activity by name and realm."""
        resource = f"/data/wow/guild/{realm_slug}/{name_slug}/activity"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_guild_achievements(self, region, locale, realm_slug, name_slug):
        """Return a single guild's achievements by name and realm."""
        resource = f"/data/wow/guild/{realm_slug}/{name_slug}/achievements"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_guild_roster(self, region, locale, realm_slug, name_slug):
        """Return a single guild's roster by its name and realm."""
        resource = f"/data/wow/guild/{realm_slug}/{name_slug}/roster"
        query_params = {"namespace": f"profile-{region}", "locale": locale}
        return super().get_resource(resource, region, query_params)
