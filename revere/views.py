from flask import render_template, request, url_for, redirect
from revere import app, db
from revere.db import Monitor, Alert
from revere.forms import MonitorForm, AlertForm
from revere.util import update_monitor_scheduler
import math


@app.route('/')
def monitor_list():
    monitors = Monitor.query.all()
    return render_template('monitor_list.html', monitors=monitors)


@app.route('/monitor/<monitor_id>')
def monitor_detail(monitor_id):
    monitor = Monitor.query.get_or_404(monitor_id)
    return render_template('monitor_detail.html', monitor=monitor)


@app.route('/monitor/<monitor_id>/history')
def monitor_history(monitor_id):
    monitor = Monitor.query.get_or_404(monitor_id)

    logs = monitor.logs.order_by('timestamp DESC')
    count = logs.count()
    per_page = 100
    last_page = math.ceil(count / float(per_page))
    page = 1

    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1

    if page > last_page:
        page = last_page
    if page < 1:
        page = 1
    page = int(page)
    page_logs = logs.limit(per_page).offset((page - 1) * per_page)

    return render_template('monitor_history.html',
                           monitor=monitor,
                           page_logs=page_logs,
                           count=count,
                           per_page=per_page,
                           last_page=last_page,
                           page=page)


@app.route('/monitor/<monitor_id>/edit', methods=['GET', 'POST'])
def monitor_edit(monitor_id):
    monitor = Monitor.query.get_or_404(monitor_id)

    form = MonitorForm(request.form, monitor)
    if form.validate_on_submit():
        form.populate_obj(monitor)
        db.session.add(monitor)
        db.session.commit()
        if not monitor.active:
            monitor.record_run('INACTIVE', 'Monitor edited', None)
        update_monitor_scheduler(monitor)
        return redirect(url_for('monitor_detail', monitor_id=monitor.id))
    return render_template('monitor_edit.html', form=form, sources=app.sources, monitor=monitor, create=False)


@app.route('/create', methods=['GET', 'POST'])
def create():
    form = MonitorForm(request.form)
    if request.method == 'POST' and form.validate():
        new_monitor = Monitor(state='INACTIVE')
        form.populate_obj(new_monitor)
        db.session.add(new_monitor)
        db.session.commit()
        update_monitor_scheduler(new_monitor)
        return redirect(url_for('monitor_detail', monitor_id=new_monitor.id))
    return render_template('monitor_edit.html', form=form, sources=app.sources, create=True)


@app.route('/alerts')
def alert_list():
    alerts = Alert.query.all()
    return render_template('alert_list.html', alerts=alerts)


@app.route('/alert/<alert_id>/edit', methods=['GET', 'POST'])
def alert_edit(alert_id):
    alert = Alert.query.get_or_404(alert_id)

    form = AlertForm(request.form, alert)
    if form.validate_on_submit():
        form.populate_obj(alert)
        db.session.add(alert)
        db.session.commit()
        return redirect(url_for('alert_list'))
    return render_template('alert_edit.html', form=form, alert=alert)
