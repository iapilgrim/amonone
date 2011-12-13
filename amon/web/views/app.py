from datetime import timedelta
from amon.core import settings
from amon.web.views.base import BaseView
from amon.web.template import render
from amon.web.utils import datestring_to_unixtime,datetime_to_unixtime
from amon.system.utils import get_disk_volumes, get_network_interfaces
from amon.web.models import (
	dashboard_model,		
	system_model,
	process_model,
	exception_model,
	log_model
)
from amon.web.decorators import logged_in

class DashboardView(BaseView):

	def initialize(self):
		super(DashboardView, self).initialize()

	@logged_in
	def get(self):

		active_process_checks = settings.PROCESS_CHECKS
		active_system_checks = settings.SYSTEM_CHECKS

		# Get the first element from the settings - used for the last check date in the template
		try:
			process_check_first = active_process_checks[0]
		except IndexError:
			process_check_first = False

		try:
			system_check_first = active_system_checks[0]
		except IndexError: 
			system_check_first = False
		
		last_system_check = dashboard_model.get_last_system_check(active_system_checks)
		last_process_check = dashboard_model.get_last_process_check(active_process_checks)

		_template = render(template="dashboard.html",
				current_page='dashboard',
				last_check=last_system_check,
				process_check=last_process_check,
				system_check_first=system_check_first,
				process_check_first=process_check_first,
				unread_values=self.unread_values
				)

		self.write(_template)

class SystemView(BaseView):

	def initialize(self):
		super(SystemView, self).initialize()

	def get(self):
		
		date_from = self.get_argument('date_from', False)
		date_to = self.get_argument('date_to', False)

		if date_from:
			date_from = datestring_to_unixtime(date_from)
		
		# Default - 24 hours period
		else:
			day = timedelta(hours=24)
			yesterday = self.now - day

			date_from = datetime_to_unixtime(yesterday)
		
		if date_to:
			date_to = datestring_to_unixtime(date_to)
		else:
			date_to = datetime_to_unixtime(self.now)
		
		active_checks = settings.SYSTEM_CHECKS
	
		checks = system_model.get_system_data(active_checks, date_from, date_to)
		first_check_date = system_model.get_first_check_date()

		if checks != False:
			network = []
			network_interfaces = []
			
			disk = []
			volumes = []
			
			# Add network adapters 
			if 'network' in active_checks:
				for check in checks['network']:
					network.append(check)	

				_interfaces = get_network_interfaces()
				for interface in _interfaces:
					if interface not in network_interfaces:
						network_interfaces.append(interface)

			# Add disk volumes
			if 'disk' in active_checks:
				for check in checks['disk']:
					disk.append(check)
			
				_volumes = get_disk_volumes()
				for volume in _volumes:
					if volume not in volumes:
						volumes.append(volume)

			_template = render(template='system.html',
						  current_page='system',
						  checks=checks,
						  network=network,
						  network_interfaces=network_interfaces,
						  volumes=volumes,
						  disk=disk,
						  date_from=date_from,
						  date_to=date_to,
						  first_check_date=first_check_date,
						  unread_values=self.unread_values
						  )

			self.write(_template)

class ProcessesView(BaseView):

	def initialize(self):
		super(ProcessesView, self).initialize()
		self.current_page = 'processes'

	def get(self):
		day = timedelta(hours=24)
		_yesterday = self.now - day

		date_from = self.get_argument('date_from', False)
		date_to = self.get_argument('date_to', False)

		if date_from:
			date_from = datestring_to_unixtime(date_from)
		else:
			date_from = datetime_to_unixtime(_yesterday)
		
		if date_to:
			date_to = datestring_to_unixtime(date_to)
		else:
			date_to = datetime_to_unixtime(self.now)

		
		processes = settings.PROCESS_CHECKS
		process_data = process_model.get_process_data(processes, date_from, date_to)


		_template = render(template='processes.html',
					  current_page=self.current_page,
					  processes=processes,
					  process_data=process_data,
					  date_from=date_from,
					  date_to=date_to,
					  unread_values=self.unread_values
					 )

		self.write(_template)


class ExceptionsView(BaseView):
	
	def initialize(self):
		super(ExceptionsView, self).initialize()
		self.current_page = 'exceptions'

	def get(self):
		
		exceptions = exception_model.get_exceptions()
		exception_model.mark_as_read()

		_template = render(template='exceptions.html',
					  exceptions=exceptions,
					  current_page=self.current_page,
					  unread_values=self.unread_values
					  )

		self.write(_template)

class LogsView(BaseView):

	def initialize(self):
		super(LogsView, self).initialize()
		self.current_page = 'logs'

	def get(self):

		logs = log_model.get_logs()
		log_model.mark_as_read()

		_template =  render(template='logs.html',
					 current_page=self.current_page,
					 logs=logs,
					 unread_values=self.unread_values,
					 )
		
		self.write(_template)


	def post(self):
		level = self.get_arguments('level[]')
		filter = self.get_argument('filter', None)

		logs = log_model.filtered_logs(level, filter)
	
		_template = render(template='partials/logs_filter.html', 
				logs=logs)

		self.write(_template)
