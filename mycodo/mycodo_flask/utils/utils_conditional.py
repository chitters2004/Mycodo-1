# -*- coding: utf-8 -*-
import logging

import os
import sqlalchemy
from flask import flash
from flask import url_for
from flask_babel import gettext

from mycodo.config import PATH_PYTHON_CODE_USER
from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import Actions
from mycodo.databases.models import Conditional
from mycodo.databases.models import ConditionalConditions
from mycodo.databases.models import DisplayOrder
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_function import check_actions
from mycodo.mycodo_flask.utils.utils_general import controller_activate_deactivate
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_misc import save_conditional_code
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger(__name__)


def conditional_mod(form):
    """Modify a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    try:
        save_conditional_code(
            error,
            form.conditional_statement.data,
            form.function_id.data,
            test=True)

        cond_mod = Conditional.query.filter(
            Conditional.unique_id == form.function_id.data).first()
        cond_mod.name = form.name.data
        cond_mod.conditional_statement = form.conditional_statement.data
        cond_mod.period = form.period.data
        cond_mod.log_level_debug = form.log_level_debug.data
        cond_mod.start_offset = form.start_offset.data
        cond_mod.refractory_period = form.refractory_period.data

        if not error:
            db.session.commit()

            if cond_mod.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(
                    form.function_id.data)
                flash(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value), "success")

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_del(cond_id):
    """Delete a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    cond = Conditional.query.filter(
        Conditional.unique_id == cond_id).first()

    # Deactivate conditional if active
    if cond.is_activated:
        conditional_deactivate(cond_id)

    try:
        if not error:
            # Delete conditions
            conditions = ConditionalConditions.query.filter(
                ConditionalConditions.conditional_id == cond_id).all()
            for each_condition in conditions:
                delete_entry_with_id(ConditionalConditions,
                                     each_condition.unique_id)

            # Delete Actions
            actions = Actions.query.filter(
                Actions.function_id == cond_id).all()
            for each_action in actions:
                delete_entry_with_id(Actions,
                                     each_action.unique_id)

            delete_entry_with_id(Conditional, cond_id)

            display_order = csv_to_list_of_str(DisplayOrder.query.first().function)
            display_order.remove(cond_id)
            DisplayOrder.query.first().function = list_to_csv(display_order)

            try:
                file_path = os.path.join(
                    PATH_PYTHON_CODE_USER, 'conditional_{}.py'.format(
                        cond.unique_id))
                os.remove(file_path)
            except:
                pass

            db.session.commit()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_condition_add(form):
    """Add a Conditional Condition"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['add']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  gettext("Condition")))

    cond = Conditional.query.filter(
        Conditional.unique_id == form.function_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before adding a Condition")

    if form.condition_type.data == '':
        error.append("Must select a condition")

    try:
        new_condition = ConditionalConditions()
        new_condition.conditional_id = form.function_id.data
        new_condition.condition_type = form.condition_type.data

        if new_condition.condition_type == 'measurement':
            new_condition.max_age = 360

        if not error:
            new_condition.save()
    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_condition_mod(form):
    """Modify a Conditional condition"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['modify']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  gettext("Condition")))

    try:
        conditional = Conditional.query.filter(
            Conditional.unique_id == form.conditional_id.data).first()

        cond_mod = ConditionalConditions.query.filter(
            ConditionalConditions.unique_id == form.conditional_condition_id.data).first()

        if cond_mod.condition_type in ['measurement',
                                       'measurement_dict']:
            error = check_form_measurements(form, error)
            cond_mod.measurement = form.measurement.data
            cond_mod.max_age = form.max_age.data

        elif cond_mod.condition_type == 'gpio_state':
            cond_mod.gpio_pin = form.gpio_pin.data

        elif cond_mod.condition_type == 'output_state':
            cond_mod.output_id = form.output_id.data

        if not error:
            db.session.commit()

            if conditional.is_activated:
                control = DaemonControl()
                return_value = control.refresh_daemon_conditional_settings(
                    form.conditional_id.data)
                flash(gettext(
                    "Daemon response: %(resp)s",
                    resp=return_value), "success")

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_condition_del(form):
    """Delete a Conditional Condition"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['delete']['title'],
        controller='{} {}'.format(TRANSLATIONS['conditional']['title'],
                                  gettext("Condition")))

    cond = Conditional.query.filter(
        Conditional.unique_id == form.conditional_id.data).first()
    if cond.is_activated:
        error.append("Deactivate the Conditional before deleting a Condition")

    try:
        if not error:
            cond_condition_id = ConditionalConditions.query.filter(
                ConditionalConditions.unique_id == form.conditional_condition_id.data).first().unique_id
            delete_entry_with_id(ConditionalConditions, cond_condition_id)

    except sqlalchemy.exc.OperationalError as except_msg:
        error.append(except_msg)
    except sqlalchemy.exc.IntegrityError as except_msg:
        error.append(except_msg)
    except Exception as except_msg:
        error.append(except_msg)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_activate(cond_id):
    """Activate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['activate']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id).all()

    for each_condition in conditions:
        # Check for errors in the Conditional settings
        error = check_cond_measurements(each_condition, error)

    conditions = ConditionalConditions.query.filter(
        ConditionalConditions.conditional_id == cond_id)
    if not conditions.count():
        error.append("No Conditions found: Add at least one Condition before activating.")

    actions = Actions.query.filter(
        Actions.function_id == cond_id)
    if not actions.count():
        error.append("No Actions found: Add at least one Action before activating.")

    for each_action in actions.all():
        error = check_actions(each_action, error)

    if not error:
        controller_activate_deactivate('activate', 'Conditional', cond_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def conditional_deactivate(cond_id):
    """Deactivate a Conditional"""
    error = []
    action = '{action} {controller}'.format(
        action=TRANSLATIONS['deactivate']['title'],
        controller=TRANSLATIONS['conditional']['title'])

    if not error:
        controller_activate_deactivate('deactivate', 'Conditional', cond_id)

    flash_success_errors(error, action, url_for('routes_page.page_function'))


def check_form_measurements(form, error):
    """Checks if the submitted form has any errors"""
    if not form.measurement.data or form.measurement.data == '':
        error.append("{meas} must be set".format(
            meas=form.measurement.label.text))
    if not form.max_age.data or form.max_age.data <= 0:
        error.append("{dir} must be greater than 0".format(
            dir=form.max_age.label.text))
    return error


def check_cond_measurements(form, error):
    """Checks if the saved variables have any errors"""
    if not form.measurement or form.measurement == '':
        error.append("Measurement must be set".format(
            meas=form.measurement))
    if not form.max_age or form.max_age <= 0:
        error.append("Max Age must be greater than 0")
    return error

