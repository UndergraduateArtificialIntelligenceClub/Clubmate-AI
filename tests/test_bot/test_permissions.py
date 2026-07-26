"""Tests for bot.permissions."""

from unittest.mock import MagicMock, patch

import discord
from discord import app_commands
import pytest

from bot.permissions import is_exec, exec_only


class TestIsExec:
    def _make_interaction(self, roles, is_member=True):
        interaction = MagicMock()
        if is_member:
            interaction.user = MagicMock(spec=discord.Member)
        else:
            interaction.user = MagicMock(spec=discord.User)
        interaction.user.roles = roles
        return interaction

    def _make_role(self, name):
        role = MagicMock()
        role.name = name
        return role

    @patch("bot.permissions.settings")
    def test_returns_true_when_exec_role_present(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        interaction = self._make_interaction([self._make_role("Member"), self._make_role("Executive")])
        assert is_exec(interaction) is True

    @patch("bot.permissions.settings")
    def test_returns_false_when_exec_role_absent(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        interaction = self._make_interaction([self._make_role("Member"), self._make_role("Admin")])
        assert is_exec(interaction) is False

    @patch("bot.permissions.settings")
    def test_case_insensitive_role_match(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        interaction = self._make_interaction([self._make_role("executive")])
        assert is_exec(interaction) is True

    @patch("bot.permissions.settings")
    def test_returns_false_for_non_member(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        interaction = self._make_interaction([], is_member=False)
        assert is_exec(interaction) is False

    @patch("bot.permissions.settings")
    def test_returns_false_for_no_roles(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        interaction = self._make_interaction([])
        assert is_exec(interaction) is False

    @patch("bot.permissions.settings")
    def test_custom_role_name(self, mock_settings):
        mock_settings.exec_role_name = "Admin"
        interaction = self._make_interaction([self._make_role("admin")])
        assert is_exec(interaction) is True


class TestExecOnly:
    @patch("bot.permissions.settings")
    def test_returns_callable(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        result = exec_only()
        assert callable(result)

    @patch("bot.permissions.settings")
    def test_decorator_passes_for_exec(self, mock_settings):
        mock_settings.exec_role_name = "Executive"
        interaction = MagicMock()
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.roles = [MagicMock(name="Executive")]
        interaction.user.roles[0].name = "Executive"

        decorator = exec_only()
        assert callable(decorator)
