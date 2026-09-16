from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def color_visibility(c1, c2, size):   # later: implement rgba support
    color1 = c1.copy()
    color2 = c2.copy()
    for color, value in color1.items():
        color1[color] /= 255
    for color, value in color2.items():
        color2[color] /= 255
    
    color_luminance1 = (color1['r']**2 * 0.2126 + color1['g']**2 * 0.7152 + color1['b']**2 * 0.0722)
    color_luminance2 = (color2['r']**2 * 0.2126 + color2['g']**2 * 0.7152 + color2['b']**2 * 0.0722)
    relative_contrast = (max(color_luminance1, color_luminance2)+0.05)/(min(color_luminance1, color_luminance2)+0.05)
    if(size>=24):
        return 1*(relative_contrast>=4.5)
    elif(size>=0):
        return 1*(relative_contrast>=7)
    else:
        return 1*(relative_contrast>=3)

def translate_color(color, parent_color):
    res = {'r': 0, 'g': 0, 'b': 0}
    if color[0:4]=='rgb(':
        values = [0,0,0]
        values = color[4:color.find(')')].split(', ')
        res['r'] = float(values[0])
        res['g'] = float(values[1])
        res['b'] = float(values[2])
    elif color[0:5]=='rgba(':          
        values = [0,0,0,0]
        values = color[5:color.find(')')].split(', ')
        res['r'] = (1 - float(values[3])) * parent_color['r'] + float(values[3]) * float(values[0])
        res['g'] = (1 - float(values[3])) * parent_color['g'] + float(values[3]) * float(values[1])
        res['b'] = (1 - float(values[3])) * parent_color['b'] + float(values[3]) * float(values[2])
    return res


def color_difference(color1, color2):   # later: implement rgba support
    return 1*((abs(color1['r']-color2['r']) + abs(color1['g']-color2['g']) + abs(color1['b']-color2['b']))>500)


def calc_weights(url, driver):
    body = driver.find_element("tag name", "body")

    elements = []
    
    def rec(elem, parent_style, parent_index):
        elements.append({
            "tag": elem.tag_name,
            "parent_id": parent_index,
            "weight": 0,
            "id": 0,
            "text": driver.execute_script("""
                const text = Array.from(arguments[0].childNodes)
                    .filter(node => node.nodeType === Node.TEXT_NODE)
                    .map(node => node.textContent.trim())
                    .join(' ');
                return text;""", elem)
        })
        element_index = len(elements)-1
        if(elements[element_index]["tag"]=="script"):
            elements[element_index]["text"]=""

        elements[element_index]['id'] = element_index
        driver.execute_script('arguments[0].dataset.id=' + str(element_index), elem)
        
        computed_style = driver.execute_script(
        """let style = window.getComputedStyle(arguments[0]);
        let res = {
            "width": style['width'],
            "height": style['height'],
            "background": style['background'],
            "color": style['color'],
            "display": style["display"],
            "border-width": style["border-width"],
            "border-style": style["border-style"],
            "border-color": style["border-color"],
            "outline-width": style["outline-width"],
            "outline-style": style["outline-style"],
            "outline-color": style["outline-color"],
            "visibility": style["visibility"],
            "font-size": style["font-size"],
            "cursor": style["cursor"],
            }
        return res""",elem)
        weight = {
            'background': 0,
            'font': 0,
            'border': 0,
            'size': 0,
            'clickable': 0
        }     
        final_weight=0
        
        if(computed_style['display']!='none' and computed_style['visibility']!='hidden'):
            
            #process background
            computed_style['background'] = translate_color(computed_style['background'], parent_style['background'])
            weight['background'] = color_visibility(computed_style['background'],parent_style['background'],0)

            #process font
            computed_style['color'] = translate_color(computed_style['color'], computed_style['background'])
            computed_style['font-size'] = float(computed_style['font-size'].replace('px', ''))
            weight['font'] = color_visibility(computed_style['color'],computed_style['background'],computed_style['font-size'])
           
            #process border
            weight_border=0
            weight_outline=0
            if(computed_style['border-width']!= '0px' and computed_style['border-style']!= 'none'):
                computed_style['border-color'] = translate_color(computed_style['border-color'], parent_style['background'])
                weight_border = color_visibility(computed_style['border-color'],parent_style['background'],0)*color_visibility(computed_style['border-color'],computed_style['background'],0)
            if(computed_style['outline-width']!= '0px' and computed_style['outline-style']!= 'none'):
                computed_style['outline-color'] = translate_color(computed_style['outline-color'], parent_style['background'])
                weight_outline = color_visibility(computed_style['outline-color'],parent_style['background'],0)*color_visibility(computed_style['outline-color'],computed_style['background'],0)
            weight['border'] = max(weight_outline, weight_border)
            
            #process size
            window_size = 1920*1080
            if(computed_style['width']=='auto'):
                if(computed_style['display']=='block' or computed_style['display']=='inline-block'):
                    computed_style['width'] = parent_style['width']
                else: 
                    computed_style['width'] = len(elem.text) * computed_style['font-size'] / 2
            elif('%' in computed_style['width']):
                computed_style['width'] = parent_style['width'] * float(computed_style['width'].replace('%',''))/100
            else:
                computed_style['width'] = float(computed_style['width'].replace('px', ''))

            if(computed_style['width']!=0):
                if(computed_style['height']=='auto'):
                    computed_style['height'] = computed_style['font-size'] * (len(elem.text) * computed_style['font-size'] / (2 * computed_style['width']))
                elif('%' in computed_style['height']):
                    computed_style['height'] = parent_style['height'] * float(computed_style['height'].replace('%',''))/100
                else:
                    computed_style['height'] = float(computed_style['height'].replace('px', ''))
            else: 
                computed_style['height'] = 0
            element_size = computed_style['width']*computed_style['height']
            weight['size'] = (element_size/window_size)**(1/3)

            #process clickability
            clickable_tags = ['a', 'button', 'input', 'label']
            if(elem.tag_name in clickable_tags or computed_style['cursor'] == 'pointer' or elem.get_attribute('onclick')!=None):
                weight['clickable'] = 1
                
            final_weight = weight['size']*(weight['background'] * 0.4 + weight['font'] * 0.2 + weight['border'] * 0.2 + weight['clickable'] * 0.1 + parent_style['weight'] * 0.1)
            final_weight = round(final_weight, 4)
            #print(elem.tag_name, weight, final_weight)
            #print('----------------------------------------')
            driver.execute_script("arguments[0].setAttribute('weight', arguments[2])", elem, final_weight);
            
            children = elem.find_elements(By.XPATH, "./*")
            computed_style['weight'] = final_weight
            elements[element_index]['weight'] = final_weight
            for child in children:
                rec(child, computed_style, element_index)
        driver.execute_script("arguments[0].setAttribute('weight', arguments[2])", elem, final_weight);
    
    rec(body, {"width": body.size["width"],
            "height":  body.size["height"],
            "background": {'r':0, 'g': 0, 'b': 0},
            "color": {'r':0, 'g': 0, 'b': 0},
            "weight": 0
            }, -1)
    
    for e in list(elements): 
        if e['tag']=='script' or e['tag']=='noscript':
            elements.remove(e)
    

    #driver.quit()
    return elements