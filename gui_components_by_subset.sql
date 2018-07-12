select lt.LabelName, count(l.LabelType), i.Subset
from labels as l 
left join images as i on i.ImageId = l.ImageId 
left join label_types as lt ON lt.LabelTypeId = l.LabelType
WHERE i.Subset != 'none' AND i.Dataset != 'web'
group by l.LabelType, i.Subset
order by i.Subset, l.LabelType;