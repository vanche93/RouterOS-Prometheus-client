from argparse import ArgumentParser

import routeros_api
import configparser
import argparse
from re import match
from datetime import timedelta
from http.server import HTTPServer
from prometheus_client import MetricsHandler
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY, InfoMetricFamily
from prometheus_client import start_http_server


class RosApi:

    def __init__(self, **kwargs):
        self.routerboard_name = kwargs.pop('routerboard_name')
        self.interface = kwargs.pop('interface')
        self.wireless = kwargs.pop('wireless')
        self.caps_man = kwargs.pop('caps_man')
        self.l2tp = kwargs.pop('l2tp')
        self.gre = kwargs.pop('gre')
        try:
            self.connection = routeros_api.RouterOsApiPool(**kwargs)
            self.connection.socket_timeout = 1
            self.api = self.connection.get_api()
        except routeros_api.exceptions.RouterOsApiConnectionError as e:
            raise ConnectionError(f'{self.routerboard_name} is not connected: {e}')

    def reconnect(self):
        try:
            if self.connection.connected is False:
                print(f'Try connect to {self.routerboard_name}')
                self.api = self.connection.get_api()
                print(f'Connected to {self.routerboard_name}')
        except routeros_api.exceptions.RouterOsApiConnectionError as e:
            print(f'{self.routerboard_name} is not connected: {e}')

    def create_list_dictionaries(self, dicts):
        new_list = []
        for d in dicts:
            new_dict = {'routerboard_name': self.routerboard_name}
            for key, value in d.items():
                new_dict[key.replace('-', '_')] = d.get(key)
            new_list.append(new_dict)
        return new_list

    def routerboard(self):
        routerboard = self.api.get_resource('/system/routerboard').get()
        return self.create_list_dictionaries(routerboard)

    def health(self):
        health = self.api.get_resource('/system/health').get()
        return self.create_list_dictionaries(health)

    def system_identity(self):
        system_identity = self.api.get_resource('/system/identity').get()
        return self.create_list_dictionaries(system_identity)

    def dhcp_lease(self):
        dhcp_lease = self.api.get_resource('/ip/dhcp-server/lease').get()
        return self.create_list_dictionaries(dhcp_lease)

    def dhcp_lease_count(self):
        count = [{'count': len(self.dhcp_lease())}]
        return self.create_list_dictionaries(count)

    def dhcp_bound_lease_count(self):
        count = 0
        for d in self.dhcp_lease():
            if d.get('status') == 'bound':
                count = count + 1
        return self.create_list_dictionaries([{'count': count}])

    @staticmethod
    def parse_uptime(time):
        time = match(r'((?P<weeks>\d+)w)?((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?',
                     time)
        time = time.groupdict()
        time_params = {}
        for (key, value) in time.items():
            if value:
                time_params[key] = int(value)
        return timedelta(**time_params).total_seconds()

    def system_resource(self):
        system_resource = self.api.get_resource('/system/resource').get()
        system_resource[0]['uptime'] = self.parse_uptime(system_resource[0]['uptime'])
        return self.create_list_dictionaries(system_resource)

    def interface_traffic(self):
        interface_traffic_list = []
        if self.interface == 'True':
            for interface in self.interface_list():
                if interface['running'] == 'true':
                    traffic = self.api.get_resource('/interface').call('monitor-traffic',
                                                                       {'interface': interface['name'], 'once': ''})[0]
                    if interface.get('comment'):
                        traffic['name'] = f'''{interface['name']}({interface['comment']})'''
                    interface_traffic_list.append(traffic)
        return self.create_list_dictionaries(interface_traffic_list)

    def interface_list(self):
        interface_list = self.api.get_resource('/interface/ethernet').get()
        return interface_list

    def caps_man_interface_list(self):
        interface_list = self.api.get_resource('/caps-man/interface').get()
        return interface_list

    def caps_man_traffic(self):
        caps_man_traffic_list = []
        if self.caps_man == 'True':
            for interface in self.caps_man_interface_list():
                if interface['running'] == 'true':
                    traffic = self.api.get_resource('/interface').call('monitor-traffic',
                                                                       {'interface': interface['name'], 'once': ''})[0]
                    caps_man_traffic_list.append(traffic)
        return self.create_list_dictionaries(caps_man_traffic_list)

    def wireless_interface_list(self):
        interface_list = self.api.get_resource('/interface/wireless').get()
        return interface_list

    def wireless_traffic(self):
        wireless_traffic_list = []
        if self.wireless == 'True':
            for interface in self.wireless_interface_list():
                if interface['running'] == 'true':
                    traffic = self.api.get_resource('/interface').call('monitor-traffic',
                                                                       {'interface': interface['name'], 'once': ''})[0]
                    wireless_traffic_list.append(traffic)
        return self.create_list_dictionaries(wireless_traffic_list)

    def gre_traffic(self):
        gre_traffic_list = []
        if self.gre == 'True':
            for interface in self.gre_list():
                if interface['running'] == 'true':
                    traffic = self.api.get_resource('/interface').call('monitor-traffic',
                                                                       {'interface': interface['name'], 'once': ''})[0]
                    gre_traffic_list.append(traffic)
        return self.create_list_dictionaries(gre_traffic_list)

    def gre_list(self):
        interface_list = self.api.get_resource('/interface/gre').get()
        return interface_list

    def l2tp_server_traffic(self):
        l2tp_server_traffic_list = []
        if self.l2tp == 'True':
            for interface in self.l2tp_server_list():
                if interface['running'] == 'true':
                    traffic = self.api.get_resource('/interface').call('monitor-traffic',
                                                                       {'interface': interface['name'], 'once': ''})[0]
                    l2tp_server_traffic_list.append(traffic)
        return self.create_list_dictionaries(l2tp_server_traffic_list)

    def l2tp_server_list(self):
        interface_list = self.api.get_resource('/interface/l2tp-server').get()
        return interface_list

    def l2tp_server_count(self):
        count = []
        if self.l2tp == 'True':
            count = [{'count': len(self.l2tp_server_list())}]
        return self.create_list_dictionaries(count)


class RouterOSCollector(object):

    def __init__(self, nodes=[]):
        count = 0
        for node in nodes:
            var = RosApi(**node)
            var_name = f'r{count}'
            setattr(self, var_name, var)
            count = count + 1

    @staticmethod
    def create_gauge_collector(name, info, dicts, value_key, labels=[]):
        labels.append('routerboard_name')
        if type(dicts) is list:
            collector = GaugeMetricFamily(f'routeros_{name}', info, labels=labels)
            for d in dicts:
                labels_values = []
                for label in labels:
                    labels_values.append(d.get(label))
                collector.add_metric(labels_values, d.get(value_key, 0))
            return collector
        else:
            raise Exception(f'{type(dicts)} is not a list of dictionaries.')

    @staticmethod
    def create_info_collector(name, info, dicts, labels=[]):
        labels.append('routerboard_name')
        if type(dicts) is list:
            collector = InfoMetricFamily(f'routeros_{name}', info)
            for d in dicts:
                labels_values = {}
                for label in labels:
                    if d.get(label):
                        labels_values[label] = d.get(label)
                    else:
                        labels_values[label] = ''
                collector.add_metric(labels, labels_values)
            return collector
        else:
            raise Exception(f'{type(dicts)} is not a dictionary or a list of dictionaries.')

    def get(self, func):
        output = []
        for r in self.__dict__.values():
            try:
                if r.connection.connected:
                    output = output + func(r)
            except routeros_api.exceptions.RouterOsApiConnectionError:
                pass
        return output

    def reconnect(self):
        for r in self.__dict__.values():
            r.reconnect()

    def collect(self):
        # metrics
        interface_traffic = self.get(func=RosApi.interface_traffic)
        wireless_traffic = self.get(func=RosApi.caps_man_traffic) + self.get(func=RosApi.wireless_traffic)
        gre_traffic = self.get(func=RosApi.gre_traffic)
        l2tp_server_traffic = self.get(func=RosApi.l2tp_server_traffic)
        system_resource = self.get(RosApi.system_resource)
        health = self.get(RosApi.health)
        l2tp_server_count = self.get(RosApi.l2tp_server_count)
        yield self.create_gauge_collector('rx_bits_per_second', 'rx_bits_per_second from monitor_traffic',
                                          interface_traffic, 'rx_bits_per_second', ['name'])
        yield self.create_gauge_collector('tx_bits_per_second', 'tx_bits_per_second from monitor_traffic',
                                          interface_traffic, 'tx_bits_per_second', ['name'])
        yield self.create_gauge_collector('wifi_rx_bits_per_second', 'rx_bits_per_second from monitor_traffic',
                                          wireless_traffic, 'rx_bits_per_second', ['name'])
        yield self.create_gauge_collector('wifi_tx_bits_per_second', 'tx_bits_per_second from monitor_traffic',
                                          wireless_traffic, 'tx_bits_per_second', ['name'])
        yield self.create_gauge_collector('gre_rx_bits_per_second', 'rx_bits_per_second from monitor_traffic',
                                          gre_traffic, 'rx_bits_per_second', ['name'])
        yield self.create_gauge_collector('gre_tx_bits_per_second', 'tx_bits_per_second from monitor_traffic',
                                          gre_traffic, 'tx_bits_per_second', ['name'])
        yield self.create_gauge_collector('l2tp_server_rx_bits_per_second', 'rx_bits_per_second from monitor_traffic',
                                          l2tp_server_traffic, 'rx_bits_per_second', ['name'])
        yield self.create_gauge_collector('l2tp_server_tx_bits_per_second', 'tx_bits_per_second from monitor_traffic',
                                          l2tp_server_traffic, 'tx_bits_per_second', ['name'])
        yield self.create_gauge_collector('l2tp_server_count', 'client counter on the server',
                                          l2tp_server_count, 'count')
        yield self.create_gauge_collector('free_memory', 'free_memory', system_resource, 'free_memory')
        yield self.create_gauge_collector('total_memory', 'total_memory', system_resource, 'total_memory')
        yield self.create_gauge_collector('cpu_load', 'cpu_load', system_resource, 'cpu_load')
        yield self.create_gauge_collector('free_hdd_space', 'free_hdd_space', system_resource, 'free_hdd_space')
        yield self.create_gauge_collector('uptime', 'uptime(seconds)', system_resource, 'uptime')
        yield self.create_gauge_collector('routerboard_voltage', 'routerboard_voltage', health, 'voltage')
        yield self.create_gauge_collector('routerboard_temperature', 'routerboard_temperature', health, 'temperature')
        yield self.create_gauge_collector('dhcp_lease_count', 'dhcp_lease_count', self.get(RosApi.dhcp_lease_count),
                                          'count')
        yield self.create_gauge_collector('dhcp_bound_lease_count', 'dhcp_bound_lease_count',
                                          self.get(RosApi.dhcp_bound_lease_count),
                                          'count')
        # info
        yield self.create_info_collector('system_identity', 'system_identity', self.get(RosApi.system_identity),
                                         ['name'])
        yield self.create_info_collector('routerboard', 'routerboard_info', self.get(RosApi.routerboard),
                                         ['routerboard_name', 'routerboard', 'board_name', 'model', 'serial_number',
                                          'firmware_type', 'factory_firmware', 'current_firmware', 'upgrade_firmware']
                                         )
        self.reconnect()


def run(server_class=HTTPServer, handler_class=MetricsHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def config_read(config_path=None):
    config = configparser.ConfigParser()
    config.read(config_path)
    routerboard_list = []
    for sect in config.sections():
        routerboard = {'routerboard_name': sect}
        for name, value in config.items(sect):
            routerboard[name] = value
        routerboard_list.append(routerboard)
    return routerboard_list


def main():
    parser = argparse.ArgumentParser(description='RouterOS-prometheus-export')
    parser.add_argument('-c', '--config', dest='config', type=str, required=True, help='Pass in a configuration file')
    parser.add_argument('-p', '--port', dest='port', type=int, required=True, help='HTTPServer port')
    args = parser.parse_args()
    REGISTRY.register(RouterOSCollector(nodes=config_read(args.config)))
    run(port=args.port)


if __name__ == '__main__':
    main()
