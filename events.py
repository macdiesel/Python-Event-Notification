'''
Copyright (c) 2011 Brian Beggs

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
'''
from multiprocessing.dummy import Pool
from threading import RLock

subscribers = []
pool = Pool(processes=2)
priority_pool = Pool(processes=1)

listenerLock = RLock()

def synchronized(lock):
    '''Synchronization decorator, borrowed from http://wiki.python.org/moin/PythonDecoratorLibrary#Synchronization'''
    def decorator(func):
        def wraper(*args, **kwargs):
            lock.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()

        return wraper
    return decorator


@synchronized(listenerLock)
def add_event_listener(handler, event_service=None, event_name=None):
    match = EventMatch(handler, event_service, event_name) 
    subscribers.append(match)
    return match
    
@synchronized(listenerLock)
def remove_event_listener(match):
    subscribers.remove(match)
        
@synchronized(listenerLock)
def fire_event(event_message, priority):
    for sub in subscribers:
        if priority >= 2:
            pool.apply_async(func=sub.handle_event, args=[event_message,])
        else:
            priority_pool.apply_async(func=sub.handle_event, args=[event_message,])
            
            
            
class EventMatch(object):
    def __init__(self, handler, event_service=None, event_name=None):
        self._handler = handler
        self._event_service = event_service
        self._event_name = event_name
        
    def should_handle_event(self, event_service, event_name):
        handle_event = False
        if (self._event_service is None or self._event_service == event_service) and (self._event_name is None or self._event_name == event_name):
            handle_event = True
        return handle_event
    
    def handle_event(self, event_message):
        if self.should_handle_event(event_message.event_service, event_message.event_name):
            self._handler(*event_message.args)
        
    def remove(self):
        remove_event_listener(self)
        
    def __hash__(self):
        return hash(id(self))
    
    def __eq__(self, other):
        return self is other
    
    def __ne__(self, other):
        return self is not other
    
    
class EventMessage(object):
    def __init__(self, event_service, event_name=None):
        self.event_service = event_service
        self.event_name = event_name
        self.args = []
        
    def append(self, *args):
        for arg in args:
            self.args.append(arg)
            
def event(event_service, priority=5):
    ''' Decorator used to have a method put an event on to the event queue '''    
    def decorator(func):
        event_name = func.__name__
        
        def do_fire_event(self, *args, **kwargs):
            func(self, *args, **kwargs)
            event_message = EventMessage(event_service, event_name)
            event_message.append(*args)
            fire_event(event_message, priority)
        
        return do_fire_event
        
    return decorator    

